#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_json_from_stdout(text: str) -> Optional[dict]:
    raw = text.strip()
    if not raw:
        return None
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    candidates = [raw]
    if lines:
        candidates.extend(reversed(lines))

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
            if isinstance(payload, dict):
                return payload
        except Exception:
            continue
    return None


def load_keywords(path: Path, keyword_column: str) -> List[str]:
    keywords: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if keyword_column not in set(reader.fieldnames or []):
            raise ValueError(f"CSV 缺少列: {keyword_column}")
        for row in reader:
            keyword = str(row.get(keyword_column) or "").strip()
            if keyword:
                keywords.append(keyword)
    return keywords


def load_first_level_links(path: Path) -> List[str]:
    if not path.exists():
        return []
    links: List[str] = []
    seen = set()
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            link = str(row.get("url") or "").strip()
            if link and link not in seen:
                seen.add(link)
                links.append(link)
    return links


def write_markdown(path: Path, report: Dict) -> None:
    lines = [
        "# 批量关键词标准路径执行报告",
        "",
        f"- started_at: `{report['started_at']}`",
        f"- finished_at: `{report['finished_at']}`",
        f"- keyword_total: `{report['keyword_total']}`",
        f"- succeeded: `{report['succeeded']}`",
        f"- blocked: `{report['blocked']}`",
        f"- failed: `{report['failed']}`",
        f"- queue_link_count: `{report['queue_link_count']}`",
        f"- queue_csv: `{report['queue_csv']}`",
        "",
        "## 明细",
        "",
        "| keyword | status | top10 | first_level | selected_url | run_dir |",
        "|---|---:|---:|---:|---|---|",
    ]

    for item in report.get("items", []):
        lines.append(
            "| {keyword} | {status} | {top10} | {first_level} | {selected_url} | {run_dir} |".format(
                keyword=item.get("keyword", ""),
                status=item.get("status", ""),
                top10=item.get("top10_count", 0),
                first_level=item.get("first_level_link_count", 0),
                selected_url=item.get("selected_url", "") or "N/A",
                run_dir=item.get("run_dir", "") or "N/A",
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run_one_keyword(
    standard_script: Path,
    keyword: str,
    pick_rank: int,
    out_root: Path,
    pwcli: str,
    session: str,
    privacy_mode: str,
    pw_timeout_s: int,
    sleep_ms: int,
) -> Tuple[Dict, Optional[str]]:
    cmd = [
        "python3",
        str(standard_script),
        "--keyword",
        keyword,
        "--pick-rank",
        str(max(pick_rank, 1)),
        "--out-root",
        str(out_root),
        "--session",
        session,
        "--privacy-mode",
        privacy_mode,
        "--pw-timeout-s",
        str(max(pw_timeout_s, 10)),
        "--sleep-ms",
        str(max(sleep_ms, 0)),
    ]
    if pwcli:
        cmd.extend(["--pwcli", pwcli])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}, result.stderr.strip() or "keyword standard path failed"

    payload = parse_json_from_stdout(result.stdout)
    if not payload:
        return {}, "无法从标准路径脚本输出中解析 summary json"
    return payload, None


def build_short_session_id(session_prefix: str, idx: int, keyword: str) -> str:
    # Keep unix socket path short; playwright-cli stores session id in socket filename.
    prefix = "".join(ch for ch in session_prefix if ch.isalnum()).lower()[:6] or "wx"
    digest = hashlib.sha1(keyword.encode("utf-8")).hexdigest()[:6]
    return f"{prefix}{idx:02d}{digest}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch run standard path for keyword list and generate queue CSV.")
    parser.add_argument(
        "--keywords-csv",
        default="data/wechat-research/keywords_novel_to_storyboard_top10.csv",
        help="keywords csv path",
    )
    parser.add_argument("--keyword-column", default="keyword", help="column name for keyword")
    parser.add_argument("--pick-rank", type=int, default=1, help="pick one from top10 (1-based)")
    parser.add_argument("--limit", type=int, default=0, help="max keywords to process, 0 means all")
    parser.add_argument("--start-index", type=int, default=1, help="1-based start index")
    parser.add_argument(
        "--top-links-per-keyword",
        type=int,
        default=30,
        help="max first-level links added into queue per keyword",
    )
    parser.add_argument(
        "--out-root",
        default="output/wechat-research/keyword-path",
        help="output root for per-keyword runs",
    )
    parser.add_argument(
        "--batch-out-dir",
        default="output/wechat-research/keyword-path-batch",
        help="batch report output root",
    )
    parser.add_argument(
        "--queue-dir",
        default="data/wechat-research/queue",
        help="queue directory for generated keyword,url csv",
    )
    parser.add_argument(
        "--queue-prefix",
        default="keyword-path-batch",
        help="generated queue csv file prefix",
    )
    parser.add_argument(
        "--standard-script",
        default="scripts/wechat_keyword_standard_path.py",
        help="standard path script path",
    )
    parser.add_argument("--pwcli", default="", help="path to playwright_cli.sh")
    parser.add_argument("--session-prefix", default="wx_keyword_batch", help="session prefix")
    parser.add_argument(
        "--privacy-mode",
        choices=["incognito", "normal"],
        default="incognito",
        help="incognito clears browser storage before/after each keyword run",
    )
    parser.add_argument("--pw-timeout-s", type=int, default=60, help="timeout for each pwcli call")
    parser.add_argument("--sleep-ms", type=int, default=600, help="sleep between keywords")
    parser.add_argument(
        "--include-selected-url-if-empty",
        action="store_true",
        help="if first-level links are empty, include selected_url into queue",
    )
    args = parser.parse_args()

    root = resolve_root()
    keywords_csv = (root / args.keywords_csv).resolve() if not Path(args.keywords_csv).is_absolute() else Path(args.keywords_csv)
    out_root = (root / args.out_root).resolve() if not Path(args.out_root).is_absolute() else Path(args.out_root)
    batch_out_root = (
        (root / args.batch_out_dir).resolve() if not Path(args.batch_out_dir).is_absolute() else Path(args.batch_out_dir)
    )
    queue_dir = (root / args.queue_dir).resolve() if not Path(args.queue_dir).is_absolute() else Path(args.queue_dir)
    standard_script = (
        (root / args.standard_script).resolve()
        if not Path(args.standard_script).is_absolute()
        else Path(args.standard_script)
    )

    if not keywords_csv.exists():
        raise ValueError(f"关键词 CSV 不存在: {keywords_csv}")
    if not standard_script.exists():
        raise ValueError(f"标准路径脚本不存在: {standard_script}")

    keywords = load_keywords(keywords_csv, args.keyword_column)
    if not keywords:
        raise ValueError("未读取到关键词")

    start_index = max(args.start_index, 1)
    selected = keywords[start_index - 1 :]
    if args.limit > 0:
        selected = selected[: args.limit]
    if not selected:
        raise ValueError("start-index 超出关键词数量")

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    batch_dir = batch_out_root / f"batch-{ts}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    out_root.mkdir(parents=True, exist_ok=True)
    queue_dir.mkdir(parents=True, exist_ok=True)

    queue_csv = queue_dir / f"{args.queue_prefix}-{ts}.csv"
    queue_rows: List[Tuple[str, str]] = []
    queue_seen_urls = set()
    items: List[Dict] = []

    started_at = now_iso()
    for idx, keyword in enumerate(selected, start=1):
        session = build_short_session_id(args.session_prefix, idx, keyword)
        summary, error = run_one_keyword(
            standard_script=standard_script,
            keyword=keyword,
            pick_rank=args.pick_rank,
            out_root=out_root,
            pwcli=args.pwcli,
            session=session,
            privacy_mode=args.privacy_mode,
            pw_timeout_s=args.pw_timeout_s,
            sleep_ms=args.sleep_ms,
        )

        if error:
            items.append(
                {
                    "keyword": keyword,
                    "status": "failed",
                    "error": error,
                    "top10_count": 0,
                    "first_level_link_count": 0,
                    "selected_url": "",
                    "run_dir": "",
                    "privacy_mode": args.privacy_mode,
                }
            )
            time.sleep(max(args.sleep_ms, 0) / 1000)
            continue

        run_dir = Path(str(summary.get("run_dir") or ""))
        if not run_dir.is_absolute():
            run_dir = (root / run_dir).resolve()
        links = load_first_level_links(run_dir / "first_level_links.csv")
        links = links[: max(args.top_links_per_keyword, 1)]

        selected_url = str(summary.get("selected_url") or "").strip()
        if (not links) and args.include_selected_url_if_empty and selected_url:
            links = [selected_url]

        for link in links:
            if link in queue_seen_urls:
                continue
            queue_seen_urls.add(link)
            queue_rows.append((keyword, link))

        status = "success"
        if summary.get("blocked"):
            status = "blocked"
        elif not links:
            status = "no_links"

        items.append(
            {
                "keyword": keyword,
                "status": status,
                "error": "",
                "top10_count": int(summary.get("top10_count") or 0),
                "first_level_link_count": len(links),
                "selected_url": selected_url,
                "run_dir": str(run_dir),
                "privacy_mode": str(summary.get("privacy_mode") or args.privacy_mode),
            }
        )

        time.sleep(max(args.sleep_ms, 0) / 1000)

    with queue_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["keyword", "url"])
        for keyword, url in queue_rows:
            writer.writerow([keyword, url])

    finished_at = now_iso()
    report = {
        "started_at": started_at,
        "finished_at": finished_at,
        "keyword_total": len(selected),
        "succeeded": sum(1 for item in items if item.get("status") == "success"),
        "blocked": sum(1 for item in items if item.get("status") == "blocked"),
        "failed": sum(1 for item in items if item.get("status") == "failed"),
        "no_links": sum(1 for item in items if item.get("status") == "no_links"),
        "queue_link_count": len(queue_rows),
        "queue_csv": str(queue_csv),
        "privacy_mode": args.privacy_mode,
        "items": items,
    }

    (batch_dir / "batch-summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(batch_dir / "batch-summary.md", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
