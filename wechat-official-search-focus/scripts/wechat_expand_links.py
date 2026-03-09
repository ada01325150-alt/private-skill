#!/usr/bin/env python3
import argparse
import csv
import html
import json
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


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


def load_seed_records(seed_glob: str) -> List[Tuple[str, str]]:
    seed: List[Tuple[str, str]] = []
    seen: Set[str] = set()
    for path in sorted(Path().glob(seed_glob)):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            keyword = str(item.get("keyword") or "小说改编分镜").strip() or "小说改编分镜"
            final_url = str(item.get("final_url") or "").strip()
            if final_url and final_url not in seen:
                seen.add(final_url)
                seed.append((keyword, final_url))
    return seed


def normalize_link(link: str) -> str:
    text = html.unescape(link.strip())
    if not text:
        return ""
    if "#" in text:
        text = text.split("#", 1)[0]
    return text


def is_wechat_article(link: str) -> bool:
    if "mp.weixin.qq.com" not in link:
        return False
    return ("/s/" in link) or ("/s?" in link)


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"seen_urls": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"seen_urls": []}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand additional WeChat article URLs from harvested pages.")
    parser.add_argument(
        "--seed-jsonl-glob",
        default="output/wechat-research/round-*/articles.jsonl",
        help="glob for harvested articles.jsonl files",
    )
    parser.add_argument("--out-csv", required=True, help="output csv path (keyword,url)")
    parser.add_argument(
        "--state-file",
        default="output/wechat-research/_daemon/expand_state.json",
        help="state file storing seen urls",
    )
    parser.add_argument("--pwcli", default="", help="path to playwright_cli.sh")
    parser.add_argument("--session", default="wx_expand_links", help="playwright session")
    parser.add_argument("--pw-timeout-s", type=int, default=60, help="timeout for each pwcli call")
    parser.add_argument("--sleep-ms", type=int, default=500, help="sleep between seed pages")
    parser.add_argument("--max-seeds", type=int, default=100, help="max seed pages to inspect")
    parser.add_argument("--max-new-links", type=int, default=500, help="max expanded links to output")
    parser.add_argument("--max-links-per-seed", type=int, default=500, help="max links extracted from one seed")
    args = parser.parse_args()

    pwcli = args.pwcli or str(Path.home() / ".codex/skills/playwright/scripts/playwright_cli.sh")
    out_csv = Path(args.out_csv)
    state_path = Path(args.state_file)

    seed_records = load_seed_records(args.seed_jsonl_glob)
    if not seed_records:
        raise ValueError("未读取到可用种子，请先跑至少一轮 harvest")

    seed_records = seed_records[: max(args.max_seeds, 1)]

    state = load_state(state_path)
    seen_urls: Set[str] = set(str(url) for url in state.get("seen_urls", []))
    for _, url in seed_records:
        seen_urls.add(url)

    expanded: List[Tuple[str, str, str]] = []
    # (keyword, url, source_seed)

    run_pwcli(pwcli, args.session, "open", "about:blank", timeout_s=args.pw_timeout_s)
    try:
        for keyword, seed_url in seed_records:
            try:
                run_pwcli(pwcli, args.session, "goto", seed_url, timeout_s=args.pw_timeout_s)
                expr = (
                    "(() => {"
                    "const bag = new Set();"
                    "document.querySelectorAll('a[href]').forEach(a => { if (a.href) bag.add(a.href); });"
                    "const html = document.documentElement ? document.documentElement.outerHTML : '';"
                    "const re = /https?:\\/\\/mp\\.weixin\\.qq\\.com\\/s(?:\\?[^\"'<>\\s]*)?/g;"
                    "let m;"
                    "while ((m = re.exec(html)) !== null) { bag.add(m[0]); if (bag.size > 2000) break; }"
                    "return {url: location.href, links: Array.from(bag)};"
                    "})()"
                )
                raw = run_pwcli(pwcli, args.session, "eval", expr, timeout_s=args.pw_timeout_s)
                payload = parse_json_after_result(raw) or {}
                links = payload.get("links") or []
                links = links[: max(args.max_links_per_seed, 1)]

                for link in links:
                    candidate = normalize_link(str(link or ""))
                    if not candidate:
                        continue
                    if not is_wechat_article(candidate):
                        continue
                    if candidate in seen_urls:
                        continue

                    seen_urls.add(candidate)
                    expanded.append((keyword, candidate, seed_url))
                    if len(expanded) >= max(args.max_new_links, 1):
                        break

                if len(expanded) >= max(args.max_new_links, 1):
                    break
            finally:
                time.sleep(max(args.sleep_ms, 0) / 1000)
    finally:
        try:
            run_pwcli(pwcli, args.session, "close", None, timeout_s=args.pw_timeout_s)
        except Exception:
            pass

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["keyword", "url"])
        for keyword, url, _ in expanded:
            writer.writerow([keyword, url])

    report = {
        "generated_at": now_iso(),
        "seed_count": len(seed_records),
        "new_link_count": len(expanded),
        "output_csv": str(out_csv),
    }

    state["seen_urls"] = sorted(seen_urls)
    state["last_report"] = report
    save_state(state_path, state)

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
