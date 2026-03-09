#!/usr/bin/env python3
import argparse
import csv
import hashlib
import html
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

TITLE_PATTERNS = [
    re.compile(r"var\s+msg_title\s*=\s*'([^']*)'", re.S),
    re.compile(r'<meta\s+property="og:title"\s+content="([^"]*)"', re.I),
    re.compile(r"<title>(.*?)</title>", re.I | re.S),
]
ACCOUNT_PATTERNS = [
    re.compile(r'var\s+nickname\s*=\s*htmlDecode\("([^"]*)"\)', re.S),
    re.compile(r'var\s+user_name\s*=\s*"([^"]*)"', re.S),
    re.compile(r'var\s+profile_nickname\s*=\s*"([^"]*)"', re.S),
]
PUBLISH_PATTERNS = [
    re.compile(r'var\s+publish_time\s*=\s*"?(\d{10})"?', re.S),
    re.compile(r'var\s+ct\s*=\s*"?(\d{10})"?', re.S),
]
CONTENT_PATTERNS = [
    re.compile(r'<div[^>]+id="js_content"[^>]*>(.*?)</div>\s*(?:<section|<div|</div>)', re.I | re.S),
    re.compile(r'<div[^>]+id="img-content"[^>]*>(.*?)</div>\s*</div>', re.I | re.S),
]

BLOCKED_MARKERS = [
    '环境异常',
    '完成验证后即可继续访问',
    'secitptpage/verify',
]

DELETED_MARKERS = [
    '该内容已被发布者删除',
    '内容因违规无法查看',
]


@dataclass
class UrlTask:
    url: str
    keyword: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_tasks(url: str, input_path: str) -> list[UrlTask]:
    tasks: list[UrlTask] = []
    if url:
        tasks.append(UrlTask(url=url.strip()))
    if input_path:
        csv_path = Path(input_path)
        with csv_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            if "url" not in fields:
                raise ValueError("CSV must contain a url column")
            for row in reader:
                article_url = (row.get("url") or "").strip()
                keyword = (row.get("keyword") or "").strip()
                if article_url:
                    tasks.append(UrlTask(url=article_url, keyword=keyword))
    if not tasks:
        raise ValueError("Provide --url or --input")
    return tasks


def fetch_html(url: str, timeout_s: int) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout_s) as response:
        return response.read().decode("utf-8", errors="ignore")


def first_match(patterns: Iterable[re.Pattern[str]], text: str) -> str:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return clean_inline(match.group(1))
    return ""


def clean_inline(text: str) -> str:
    value = html.unescape(text or "")
    value = value.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_body(fragment: str, max_chars: int) -> str:
    body = fragment or ""
    body = re.sub(r"<script[\s\S]*?</script>", " ", body, flags=re.I)
    body = re.sub(r"<style[\s\S]*?</style>", " ", body, flags=re.I)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"</p>|</section>|</li>|</h\d>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html.unescape(body)
    lines = [re.sub(r"\s+", " ", line).strip() for line in body.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if max_chars > 0:
        return text[:max_chars].rstrip()
    return text


def extract_content(html_text: str, max_chars: int) -> str:
    for pattern in CONTENT_PATTERNS:
        match = pattern.search(html_text)
        if match:
            content = normalize_body(match.group(1), max_chars)
            if content:
                return content
    return normalize_body(html_text, max_chars)


def extract_publish_time(html_text: str) -> str:
    raw = first_match(PUBLISH_PATTERNS, html_text)
    if raw.isdigit() and len(raw) == 10:
        return datetime.fromtimestamp(int(raw), tz=timezone.utc).isoformat()
    return raw


def classify_page(html_text: str) -> str:
    lowered = html_text.lower()
    if any(marker.lower() in lowered for marker in BLOCKED_MARKERS):
        return 'blocked'
    if any(marker.lower() in lowered for marker in DELETED_MARKERS):
        return 'deleted'
    return 'ok'


def safe_slug(text: str, fallback_url: str) -> str:
    base = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", text).strip("-")
    if base:
        return base[:80]
    suffix = hashlib.sha1(fallback_url.encode("utf-8")).hexdigest()[:10]
    return f"wechat-article-{suffix}"


def markdown_for_record(record: dict) -> str:
    parts = [f"# {record.get('title') or 'Untitled WeChat Article'}", ""]
    meta = [
        ("url", record.get("url") or ""),
        ("account_name", record.get("account_name") or ""),
        ("publish_time", record.get("publish_time") or ""),
        ("keyword", record.get("keyword") or ""),
        ("fetched_at", record.get("fetched_at") or ""),
    ]
    for key, value in meta:
        if value:
            parts.append(f"- {key}: {value}")
    parts.extend(["", "## Content", "", record.get("content_text") or ""])
    return "\n".join(parts).strip() + "\n"


def validate_url(url: str) -> None:
    host = (urlparse(url).netloc or "").lower()
    if "mp.weixin.qq.com" not in host:
        raise ValueError(f"unsupported host: {host}")


def process_task(task: UrlTask, out_dir: Path, max_chars: int, timeout_s: int) -> dict:
    validate_url(task.url)
    html_text = fetch_html(task.url, timeout_s=timeout_s)
    page_status = classify_page(html_text)
    if page_status == 'blocked':
        raise ValueError('blocked: verification page')
    if page_status == 'deleted':
        raise ValueError('deleted: article removed')
    title = first_match(TITLE_PATTERNS, html_text)
    account_name = first_match(ACCOUNT_PATTERNS, html_text)
    publish_time = extract_publish_time(html_text)
    content_text = extract_content(html_text, max_chars=max_chars)
    if len(content_text.strip()) < 50:
        raise ValueError('blocked_or_low_content: extracted text below minimum threshold')
    record = {
        "url": task.url,
        "keyword": task.keyword,
        "title": title,
        "account_name": account_name,
        "publish_time": publish_time,
        "content_text": content_text,
        "excerpt": content_text[:180].rstrip() + ("…" if len(content_text) > 180 else ""),
        "fetch_status": "ok",
        "fetched_at": now_iso(),
    }
    slug = safe_slug(title or account_name, task.url)
    article_path = out_dir / "articles" / f"{slug}.md"
    article_path.parent.mkdir(parents=True, exist_ok=True)
    article_path.write_text(markdown_for_record(record), encoding="utf-8")
    record["markdown_path"] = str(article_path)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Read and normalize WeChat official account articles.")
    parser.add_argument("--url", default="", help="single mp.weixin.qq.com article URL")
    parser.add_argument("--input", default="", help="CSV with url or keyword,url columns")
    parser.add_argument("--out-dir", required=True, help="output directory")
    parser.add_argument("--max-chars", type=int, default=24000, help="max chars to keep per article")
    parser.add_argument("--sleep-ms", type=int, default=300, help="sleep between batch URLs")
    parser.add_argument("--timeout-s", type=int, default=25, help="request timeout seconds")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = read_tasks(args.url, args.input)
    articles_jsonl = out_dir / "articles.jsonl"
    errors_jsonl = out_dir / "errors.jsonl"

    ok_count = 0
    error_count = 0
    with articles_jsonl.open("a", encoding="utf-8") as ok_handle, errors_jsonl.open("a", encoding="utf-8") as err_handle:
        for index, task in enumerate(tasks, start=1):
            try:
                record = process_task(task, out_dir, max_chars=args.max_chars, timeout_s=args.timeout_s)
                ok_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                ok_count += 1
            except Exception as exc:
                error_record = {
                    "url": task.url,
                    "keyword": task.keyword,
                    "fetch_status": "error",
                    "error": str(exc),
                    "fetched_at": now_iso(),
                }
                err_handle.write(json.dumps(error_record, ensure_ascii=False) + "\n")
                error_count += 1
            if index < len(tasks) and args.sleep_ms > 0:
                time.sleep(args.sleep_ms / 1000.0)

    summary = {
        "out_dir": str(out_dir),
        "articles_jsonl": str(articles_jsonl),
        "errors_jsonl": str(errors_jsonl),
        "processed": len(tasks),
        "ok": ok_count,
        "errors": error_count,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
