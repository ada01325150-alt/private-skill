#!/usr/bin/env python3
import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local sqlite index for harvested WeChat articles.")
    parser.add_argument("--input", required=True, help="articles.jsonl path")
    parser.add_argument("--out-db", required=True, help="output sqlite db path")
    parser.add_argument("--out-stats", required=True, help="output stats json path")
    parser.add_argument(
        "--quality-min-chars",
        type=int,
        default=200,
        help="minimum chars for a record to be counted as quality_unblocked",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    out_db = Path(args.out_db)
    out_stats = Path(args.out_stats)
    out_db.parent.mkdir(parents=True, exist_ok=True)
    out_stats.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    keyword_counter = Counter()
    blocked_count = 0
    quality_count = 0
    l1_count = 0
    quality_l1_count = 0
    low_content_count = 0

    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            rows.append(item)
            keyword = str(item.get("keyword") or "").strip()
            if keyword:
                keyword_counter[keyword] += 1
            blocked = bool(item.get("blocked"))
            final_url = str(item.get("final_url") or "")
            chars = int(item.get("chars") or 0)
            has_content = bool(item.get("content_path"))
            is_l1 = "mp.weixin.qq.com/s" in final_url

            if blocked:
                blocked_count += 1
            if is_l1:
                l1_count += 1
            if (not blocked) and chars < max(args.quality_min_chars, 0):
                low_content_count += 1
            if (not blocked) and has_content and chars >= max(args.quality_min_chars, 0):
                quality_count += 1
                if is_l1:
                    quality_l1_count += 1

    conn = sqlite3.connect(str(out_db))
    try:
        conn.execute("DROP TABLE IF EXISTS articles")
        conn.execute("DROP TABLE IF EXISTS articles_fts")
        conn.execute(
            """
            CREATE TABLE articles (
                id TEXT PRIMARY KEY,
                keyword TEXT NOT NULL,
                title TEXT,
                source_url TEXT,
                final_url TEXT,
                blocked INTEGER NOT NULL,
                chars INTEGER,
                content_path TEXT,
                collected_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE articles_fts USING fts5(
                id,
                keyword,
                title,
                content
            )
            """
        )

        for item in rows:
            doc_id = str(item.get("doc_id") or "")
            keyword = str(item.get("keyword") or "")
            title = str(item.get("title") or "")
            source_url = str(item.get("source_url") or "")
            final_url = str(item.get("final_url") or "")
            blocked = 1 if item.get("blocked") else 0
            chars = int(item.get("chars") or 0)
            content_path = item.get("content_path")
            collected_at = str(item.get("collected_at") or "")

            content = ""
            if not blocked and content_path:
                path = input_path.parent / str(content_path)
                if path.exists():
                    content = path.read_text(encoding="utf-8")

            conn.execute(
                """
                INSERT OR REPLACE INTO articles
                (id, keyword, title, source_url, final_url, blocked, chars, content_path, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, keyword, title, source_url, final_url, blocked, chars, content_path, collected_at),
            )
            conn.execute(
                "INSERT INTO articles_fts (id, keyword, title, content) VALUES (?, ?, ?, ?)",
                (doc_id, keyword, title, content),
            )

        conn.commit()
    finally:
        conn.close()

    stats = {
        "total_records": len(rows),
        "blocked_records": blocked_count,
        "unblocked_records": len(rows) - blocked_count,
        "quality_min_chars": max(args.quality_min_chars, 0),
        "quality_unblocked_records": quality_count,
        "l1_records": l1_count,
        "quality_l1_records": quality_l1_count,
        "low_content_records": low_content_count,
        "keyword_distribution": dict(keyword_counter.most_common()),
    }
    out_stats.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
