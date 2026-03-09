#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def build_digest(records: list[dict]) -> str:
    lines = ["# WeChat Reading Digest", ""]
    if not records:
        lines.append("No article records found.")
        return "\n".join(lines) + "\n"
    grouped: dict[str, list[dict]] = {}
    for record in records:
        key = record.get("keyword") or "未分组"
        grouped.setdefault(key, []).append(record)
    for keyword in sorted(grouped):
        lines.extend([f"## {keyword}", ""])
        for record in grouped[keyword]:
            title = record.get("title") or "Untitled"
            account_name = record.get("account_name") or ""
            publish_time = record.get("publish_time") or ""
            excerpt = record.get("excerpt") or ""
            url = record.get("url") or ""
            lines.append(f"### {title}")
            if account_name:
                lines.append(f"- account_name: {account_name}")
            if publish_time:
                lines.append(f"- publish_time: {publish_time}")
            if url:
                lines.append(f"- url: {url}")
            if excerpt:
                lines.extend(["", excerpt])
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a digest Markdown from extracted WeChat article JSONL.")
    parser.add_argument("--articles-jsonl", required=True, help="path to articles.jsonl")
    parser.add_argument("--out", required=True, help="output markdown path")
    args = parser.parse_args()

    input_path = Path(args.articles_jsonl)
    output_path = Path(args.out)
    records = load_records(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_digest(records), encoding="utf-8")
    print(json.dumps({"records": len(records), "out": str(output_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
