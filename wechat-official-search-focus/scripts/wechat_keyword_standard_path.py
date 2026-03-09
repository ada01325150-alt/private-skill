#!/usr/bin/env python3
import argparse
import csv
import json
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(keyword: str) -> str:
    text = "".join(ch if ch.isalnum() else "_" for ch in keyword.strip())
    return text.strip("_") or "keyword"


def _extract_balanced_json_chunk(text: str) -> Optional[str]:
    starts = [i for i, char in enumerate(text) if char in "[{"]
    for start in starts:
        opener = text[start]
        closer = "}" if opener == "{" else "]"
        depth = 0
        in_string = False
        escaped = False

        for pos in range(start, len(text)):
            char = text[pos]
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
                continue

            if char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    return text[start : pos + 1]
    return None


def parse_json_after_result(raw: str) -> Optional[dict]:
    marker = "### Result"
    idx = raw.find(marker)
    if idx < 0:
        return None
    frag = raw[idx + len(marker):]
    chunk = _extract_balanced_json_chunk(frag)
    if not chunk:
        return None
    try:
        value = json.loads(chunk)
    except json.JSONDecodeError:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"items": value}
    return {"value": value}


def parse_any_json(raw: str) -> Optional[dict]:
    text = raw.strip()
    if not text:
        return None

    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            return {"items": value}
        return {"value": value}
    except Exception:
        pass

    payload = parse_json_after_result(text)
    if payload:
        return payload

    for block in re.findall(r"```(?:json)?\s*([\[{].*?[\]}])\s*```", text, flags=re.IGNORECASE | re.DOTALL):
        try:
            value = json.loads(block)
            if isinstance(value, dict):
                return value
            if isinstance(value, list):
                return {"items": value}
            return {"value": value}
        except Exception:
            continue

    chunk = _extract_balanced_json_chunk(text)
    if chunk:
        try:
            value = json.loads(chunk)
            if isinstance(value, dict):
                return value
            if isinstance(value, list):
                return {"items": value}
            return {"value": value}
        except Exception:
            return None
    return None


def run_pwcli(
    pwcli: str,
    session: str,
    subcommand: str,
    payload: Optional[str] = None,
    timeout_s: int = 60,
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


def extract_search_top_candidates(pwcli: str, session: str, timeout_s: int) -> Dict:
    code = """
(page) => page.evaluate(() => {
  const anchors = Array.from(document.querySelectorAll('a[href]')).map((a, i) => {
    const rawHref = (a.getAttribute('href') || '').trim();
    let href = '';
    try {
      href = a.href || (rawHref ? new URL(rawHref, location.href).href : '');
    } catch (_) {
      href = rawHref;
    }
    return {
      index: i + 1,
      title: (a.innerText || a.textContent || '').trim().slice(0, 160),
      href
    };
  }).filter(x => x.href);
  const html = document.documentElement ? document.documentElement.outerHTML : '';
  return {
    url: location.href,
    title: (document.title || '').trim(),
    text: (document.body ? document.body.innerText : '').slice(0, 12000),
    html: html.slice(0, 150000),
    anchor_count: anchors.length,
    anchors: anchors.slice(0, 200)
  };
})
""".strip()
    raw = run_pwcli(pwcli, session, "run-code", code, timeout_s=timeout_s)
    data = parse_any_json(raw) or {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("_raw_output_preview", raw[:2000])
    return data


def extract_wechat_links_from_text(text: str) -> List[str]:
    if not text:
        return []
    patterns = [
        r"https?://mp\.weixin\.qq\.com/s(?:\?[^\s\"'<>]*)?",
        r"https?://weixin\.sogou\.com/link\?[^\s\"'<>]+",
    ]
    links: List[str] = []
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            url = match.group(0).strip().rstrip(",.;")
            if url and url not in seen:
                seen.add(url)
                links.append(url)
    return links


def pick_top10_articles(anchors: List[Dict], fallback_links: Optional[List[str]] = None) -> List[Dict]:
    picked: List[Dict] = []
    seen = set()
    for item in anchors:
        href = str(item.get("href") or "")
        title = str(item.get("title") or "").strip()
        if not href or not title:
            continue
        if href in seen:
            continue
        # 搜狗结果页常见链接：mp.weixin.qq.com/s... 或 weixin.sogou.com/link?url=...
        if ("mp.weixin.qq.com" not in href) and ("weixin.sogou.com/link" not in href):
            continue
        seen.add(href)
        picked.append({"title": title or "候选链接", "href": href})
        if len(picked) >= 10:
            break

    for href in fallback_links or []:
        candidate = str(href or "").strip()
        if not candidate or candidate in seen:
            continue
        if ("mp.weixin.qq.com" not in candidate) and ("weixin.sogou.com/link" not in candidate):
            continue
        seen.add(candidate)
        picked.append({"title": "候选链接(回退提取)", "href": candidate})
        if len(picked) >= 10:
            break

    return picked


def extract_first_level_links(pwcli: str, session: str, timeout_s: int) -> List[str]:
    code = """
(page) => page.evaluate(() => {
  const bag = new Set();
  document.querySelectorAll('a[href]').forEach(a => {
    if (a.href) bag.add(a.href);
  });
  const html = document.documentElement ? document.documentElement.outerHTML : '';
  const re = /https?:\\/\\/mp\\.weixin\\.qq\\.com\\/s(?:\\?[^"'<>\\s]*)?/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    bag.add(m[0]);
    if (bag.size > 3000) break;
  }
  return { url: location.href, links: Array.from(bag) };
})
""".strip()
    raw = run_pwcli(pwcli, session, "run-code", code, timeout_s=timeout_s)
    data = parse_any_json(raw) or {}
    links = data.get("links") or []

    if not links:
        links = extract_wechat_links_from_text(str(data.get("_raw_output_preview") or ""))

    out = []
    seen = set()
    for link in links:
        text = str(link or "").strip()
        if not text:
            continue
        if "#" in text:
            text = text.split("#", 1)[0]
        if "mp.weixin.qq.com" not in text:
            continue
        if ("/s/" not in text) and ("/s?" not in text):
            continue
        if text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def detect_blocked(search_data: Dict[str, Any]) -> bool:
    url_preview = str(search_data.get("url") or "")
    title_preview = str(search_data.get("title") or "")
    text_preview = str(search_data.get("text") or "")
    merged = "\n".join([url_preview, title_preview, text_preview])
    tokens = ["antispider", "验证码", "请依次点击", "访问过于频繁", "机器人", "安全验证"]
    return any(token in merged for token in tokens)


def write_summary(path: Path, payload: Dict) -> None:
    lines = []
    lines.append("# 关键词标准路径执行摘要")
    lines.append("")
    lines.append(f"- keyword: `{payload['keyword']}`")
    lines.append(f"- searched_at: `{payload['searched_at']}`")
    lines.append(f"- search_url: {payload['search_url']}")
    lines.append(f"- blocked: `{payload['blocked']}`")
    lines.append(f"- top10_count: `{payload['top10_count']}`")
    lines.append(f"- selected_rank: `{payload['selected_rank']}`")
    lines.append(f"- selected_url: {payload['selected_url'] or 'N/A'}")
    lines.append(f"- first_level_link_count: `{payload['first_level_link_count']}`")
    lines.append("")
    if payload.get("blocked"):
        lines.append("## 备注")
        lines.append("")
        lines.append("- 搜索页出现验证码/反爬拦截，请人工完成验证后重试。")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Standard path: keyword -> search top10 -> choose one -> first-level expansion.")
    parser.add_argument("--keyword", required=True, help="search keyword")
    parser.add_argument("--pick-rank", type=int, default=1, help="pick one from top10 (1-based)")
    parser.add_argument("--out-root", default="output/wechat-research/keyword-path", help="output root")
    parser.add_argument("--pwcli", default="", help="path to playwright_cli.sh")
    parser.add_argument("--session", default="wx_keyword_path", help="playwright session")
    parser.add_argument(
        "--privacy-mode",
        choices=["incognito", "normal"],
        default="incognito",
        help="incognito clears browser storage before/after run",
    )
    parser.add_argument("--pw-timeout-s", type=int, default=60, help="timeout seconds for pwcli calls")
    parser.add_argument("--sleep-ms", type=int, default=500, help="sleep milliseconds between steps")
    args = parser.parse_args()

    keyword = args.keyword.strip()
    if not keyword:
        raise ValueError("keyword 不能为空")

    pwcli = args.pwcli or str(Path.home() / ".codex/skills/playwright/scripts/playwright_cli.sh")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(args.out_root) / f"{slugify(keyword)}-{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    search_url = f"https://weixin.sogou.com/weixin?type=2&query={quote(keyword)}"

    top10 = []
    blocked = False
    selected_rank = max(args.pick_rank, 1)
    selected_url = ""
    first_level_links: List[str] = []

    run_pwcli(pwcli, args.session, "open", "about:blank", timeout_s=args.pw_timeout_s)
    try:
        if args.privacy_mode == "incognito":
            clear_browser_state(pwcli, args.session, args.pw_timeout_s)

        run_pwcli(pwcli, args.session, "goto", search_url, timeout_s=args.pw_timeout_s)
        time.sleep(max(args.sleep_ms, 0) / 1000)

        search_data = extract_search_top_candidates(pwcli, args.session, args.pw_timeout_s)
        search_data.setdefault("url", search_url)
        search_data.setdefault("title", "")
        search_data.setdefault("text", "")
        search_data.setdefault("anchors", [])

        (run_dir / "search_page.json").write_text(json.dumps(search_data, ensure_ascii=False, indent=2), encoding="utf-8")

        blocked = detect_blocked(search_data)

        anchors = search_data.get("anchors") or []
        fallback_links = []
        fallback_links.extend(extract_wechat_links_from_text(str(search_data.get("html") or "")))
        fallback_links.extend(extract_wechat_links_from_text(str(search_data.get("text") or "")))
        fallback_links.extend(extract_wechat_links_from_text(str(search_data.get("_raw_output_preview") or "")))
        top10 = pick_top10_articles(anchors, fallback_links=fallback_links)

        with (run_dir / "top10.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["rank", "title", "url"])
            for i, item in enumerate(top10, start=1):
                writer.writerow([i, item.get("title"), item.get("href")])

        if (not blocked) and top10 and selected_rank <= len(top10):
            selected_url = str(top10[selected_rank - 1]["href"])
            run_pwcli(pwcli, args.session, "goto", selected_url, timeout_s=args.pw_timeout_s)
            time.sleep(max(args.sleep_ms, 0) / 1000)

            first_level_links = extract_first_level_links(pwcli, args.session, args.pw_timeout_s)
            with (run_dir / "first_level_links.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["keyword", "url"])
                for link in first_level_links:
                    writer.writerow([keyword, link])

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

    summary = {
        "keyword": keyword,
        "searched_at": now_iso(),
        "search_url": search_url,
        "blocked": blocked,
        "top10_count": len(top10),
        "selected_rank": selected_rank,
        "selected_url": selected_url,
        "first_level_link_count": len(first_level_links),
        "privacy_mode": args.privacy_mode,
        "session": args.session,
        "run_dir": str(run_dir),
    }

    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(run_dir / "summary.md", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
