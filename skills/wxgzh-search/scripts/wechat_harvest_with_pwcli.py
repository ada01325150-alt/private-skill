#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import shlex
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_json_after_result(raw: str) -> Optional[dict]:
    marker = "### Result"
    idx = raw.find(marker)
    if idx < 0:
        return None
    frag = raw[idx + len(marker):]
    start = frag.find("{")
    if start < 0:
        return None

    text = frag[start:]
    depth = 0
    in_string = False
    escaped = False
    for pos, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                chunk = text[: pos + 1]
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    return None
    return None


def run_pwcli(
    pwcli: str,
    session: str,
    subcommand: str,
    payload: Optional[str] = None,
    timeout_s: int = 90,
) -> str:
    payload_part = f" {shlex.quote(payload)}" if payload else ""
    cmd = (
        f'export PLAYWRIGHT_CLI_SESSION={shlex.quote(session)}; '
        f'bash {shlex.quote(pwcli)} {subcommand}{payload_part}'
    )
    try:
        result = subprocess.run(
            ["bash", "-lc", cmd],
            capture_output=True,
            text=True,
            timeout=max(timeout_s, 10),
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"pwcli timeout: subcommand={subcommand}")
    if result.returncode != 0:
        stderr = result.stderr.strip() or "pwcli command failed"
        raise RuntimeError(stderr)
    return result.stdout


def clear_browser_state(pwcli: str, session: str, timeout_s: int) -> None:
    # Best-effort cleanup for privacy mode; ignore command-level failures.
    for cmd in ["cookie-clear", "localstorage-clear", "sessionstorage-clear"]:
        try:
            run_pwcli(pwcli, session, cmd, None, timeout_s=timeout_s)
        except Exception:
            continue


@dataclass
class UrlItem:
    keyword: str
    url: str


def load_urls(csv_path: Path) -> list[UrlItem]:
    items: list[UrlItem] = []
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"keyword", "url"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("CSV 必须包含列: keyword,url")
        for row in reader:
            keyword = (row.get("keyword") or "").strip()
            url = (row.get("url") or "").strip()
            if keyword and url:
                items.append(UrlItem(keyword=keyword, url=url))
    return items


def write_text_article(out_path: Path, title: str, url: str, keyword: str, text: str) -> None:
    content = (
        f"# {title}\n\n"
        f"- url: {url}\n"
        f"- keyword: {keyword}\n\n"
        f"## 正文\n\n"
        f"{text.strip()}\n"
    )
    out_path.write_text(content, encoding="utf-8")


def write_text_article_with_meta(
    out_path: Path,
    title: str,
    url: str,
    keyword: str,
    account_name: str,
    publish_time: str,
    text: str,
) -> None:
    content = (
        f"# {title}\n\n"
        f"- url: {url}\n"
        f"- keyword: {keyword}\n"
        f"- account_name: {account_name or 'N/A'}\n"
        f"- publish_time: {publish_time or 'N/A'}\n\n"
        f"## 正文\n\n"
        f"{text.strip()}\n"
    )
    out_path.write_text(content, encoding="utf-8")


def infer_focus_account(account_name: str, title: str, text: str) -> str:
    """
    Infer source account when page selectors do not expose account metadata.
    Keep mapping conservative to reduce false positives.
    """
    if account_name:
        return account_name

    preview = " ".join(
        part for part in [title or "", text[:1200] if text else ""] if part
    )

    patterns = [
        ("剧查查（DataEye）", ["DataEye短剧观察", "DataEye研究院", "剧查查", "DataEye"]),
        ("新腕儿", ["新腕儿", "新腕"]),
        ("漫剧有数", ["漫剧有数"]),
        ("红果短剧", ["红果短剧"]),
        ("广大大短剧笔记", ["广大大短剧笔记", "广大大"]),
    ]
    for canonical, keys in patterns:
        if any(key and key in preview for key in keys):
            return canonical
    return ""


def detect_block_reason(final_url: str, title: str, text: str, account_name: str, publish_time: str) -> str:
    url = (final_url or "").lower()
    body = text or ""
    body_l = body.lower()
    title_l = (title or "").strip().lower()

    if "antispider" in url:
        return "antispider_url"
    if "wappoc_appmsgcaptcha" in url:
        return "wechat_captcha_url"
    if "验证码" in body and "请依次点击" in body:
        return "captcha_text"
    if "访问过于频繁" in body or "环境异常" in body or "请在微信客户端打开链接" in body:
        return "wechat_access_guard"
    if title_l == "weixin official accounts platform" and len(body) <= 60:
        return "platform_placeholder"
    if "mp.weixin.qq.com/s" in url and len(body_l) < 30 and not account_name and not publish_time:
        return "no_content"
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch harvest WeChat article text via playwright-cli wrapper.")
    parser.add_argument("--input", required=True, help="CSV path with columns: keyword,url")
    parser.add_argument("--out-dir", required=True, help="output root directory")
    parser.add_argument("--pwcli", default="", help="path to playwright_cli.sh")
    parser.add_argument("--session", default="wx_harvest", help="playwright session name")
    parser.add_argument(
        "--privacy-mode",
        choices=["incognito", "normal"],
        default="incognito",
        help="incognito clears browser storage before/after harvesting",
    )
    parser.add_argument("--max-chars", type=int, default=24000, help="max extracted chars per article")
    parser.add_argument("--sleep-ms", type=int, default=800, help="sleep milliseconds between URLs")
    parser.add_argument("--pw-timeout-s", type=int, default=90, help="timeout seconds for each pwcli call")
    args = parser.parse_args()

    csv_path = Path(args.input)
    out_dir = Path(args.out_dir)
    pwcli = args.pwcli or str(Path.home() / ".codex/skills/playwright/scripts/playwright_cli.sh")

    items = load_urls(csv_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    article_dir = out_dir / "articles"
    article_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "articles.jsonl"
    error_path = out_dir / "errors.jsonl"

    run_pwcli(pwcli, args.session, "open", "about:blank", timeout_s=args.pw_timeout_s)

    try:
        if args.privacy_mode == "incognito":
            clear_browser_state(pwcli, args.session, args.pw_timeout_s)

        with jsonl_path.open("a", encoding="utf-8") as jsonl, error_path.open("a", encoding="utf-8") as errors:
            for idx, item in enumerate(items, start=1):
                record_base = {
                    "keyword": item.keyword,
                    "source_url": item.url,
                    "collected_at": now_iso(),
                }

                try:
                    run_pwcli(pwcli, args.session, "goto", item.url, timeout_s=args.pw_timeout_s)
                    code = f"""
(page) => page.evaluate(() => {{
  const pick = (selectors) => {{
    for (const sel of selectors) {{
      const el = document.querySelector(sel);
      if (!el) continue;
      const text = (el.textContent || '').trim();
      if (text) return text;
    }}
    return '';
  }};
  return {{
    title: document.title,
    url: location.href,
    account_name: pick(['#js_name', '.profile_nickname', '.wx_follow_nickname', '.account_nickname']),
    publish_time: pick(['#publish_time', '.rich_media_meta.rich_media_meta_text', '#post-date']),
    text: (document.body ? document.body.innerText : '').slice(0, {args.max_chars})
  }};
}})
""".strip()
                    raw = run_pwcli(pwcli, args.session, "run-code", code, timeout_s=args.pw_timeout_s)
                    payload = parse_json_after_result(raw)
                    if not payload:
                        raise RuntimeError("无法解析 pwcli eval 的 JSON 结果")

                    title = str(payload.get("title") or "").strip() or "Untitled"
                    final_url = str(payload.get("url") or "").strip() or item.url
                    account_name = str(payload.get("account_name") or "").strip()
                    publish_time = str(payload.get("publish_time") or "").strip()
                    text = str(payload.get("text") or "").strip()
                    account_name = infer_focus_account(account_name, title, text)
                    block_reason = detect_block_reason(final_url, title, text, account_name, publish_time)
                    blocked = bool(block_reason)

                    doc_id = hashlib.sha1(final_url.encode("utf-8")).hexdigest()[:16]
                    md_rel = f"articles/{doc_id}.md"
                    md_path = out_dir / md_rel

                    if not blocked and text:
                        write_text_article_with_meta(
                            md_path,
                            title=title,
                            url=final_url,
                            keyword=item.keyword,
                            account_name=account_name,
                            publish_time=publish_time,
                            text=text,
                        )

                    record = {
                        **record_base,
                        "rank": idx,
                        "privacy_mode": args.privacy_mode,
                        "doc_id": doc_id,
                        "title": title,
                        "account_name": account_name,
                        "publish_time": publish_time,
                        "final_url": final_url,
                        "blocked": blocked,
                        "block_reason": block_reason,
                        "chars": len(text),
                        "content_path": md_rel if (not blocked and text) else None,
                    }
                    jsonl.write(json.dumps(record, ensure_ascii=False) + "\n")

                except Exception as exc:
                    err = {**record_base, "rank": idx, "privacy_mode": args.privacy_mode, "error": str(exc)}
                    errors.write(json.dumps(err, ensure_ascii=False) + "\n")

                time.sleep(max(args.sleep_ms, 0) / 1000)
    finally:
        try:
            if args.privacy_mode == "incognito":
                clear_browser_state(pwcli, args.session, args.pw_timeout_s)
        except Exception:
            pass
        try:
            run_pwcli(pwcli, args.session, "close", None, timeout_s=args.pw_timeout_s)
        except Exception:
            pass


if __name__ == "__main__":
    main()
