#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate queue CSV skeletons from keyword list.")
    parser.add_argument("--input", required=True, help="keyword csv path (columns: keyword,goal)")
    parser.add_argument("--out-dir", required=True, help="queue directory")
    parser.add_argument("--batch-size", type=int, default=10, help="keywords per queue file")
    parser.add_argument("--prefix", default="round-batch", help="queue file prefix")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    keywords = []
    with input_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            kw = (row.get("keyword") or "").strip()
            if kw:
                keywords.append(kw)

    if not keywords:
        raise ValueError("未读取到关键词")

    batch_size = max(args.batch_size, 1)
    chunk_index = 1
    for start in range(0, len(keywords), batch_size):
        chunk = keywords[start:start + batch_size]
        out_file = out_dir / f"{args.prefix}-{chunk_index:03d}.csv"
        with out_file.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["keyword", "url"])
            for kw in chunk:
                writer.writerow([kw, ""])
        chunk_index += 1

    print(f"generated={chunk_index - 1} files in {out_dir}")


if __name__ == "__main__":
    main()

