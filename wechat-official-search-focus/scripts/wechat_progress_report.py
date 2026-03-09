#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build progress report for 2000-article target.")
    parser.add_argument("--root", required=True, help="output/wechat-research root directory")
    parser.add_argument("--target", type=int, default=2000, help="target article count")
    parser.add_argument(
        "--count-field",
        default="unblocked_records",
        help="stats field to aggregate (e.g., unblocked_records or quality_unblocked_records)",
    )
    parser.add_argument("--out", required=True, help="output json report path")
    args = parser.parse_args()

    root = Path(args.root)
    total = 0
    rounds = []

    for child in sorted(root.iterdir() if root.exists() else []):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        stats_file = child / "index" / "stats.json"
        if not stats_file.exists():
            continue
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
        count = int(stats.get(args.count_field, stats.get("unblocked_records", 0)))
        total += count
        rounds.append({"round": child.name, args.count_field: count})

    progress = {
        "target": args.target,
        "count_field": args.count_field,
        "current": total,
        "remaining": max(args.target - total, 0),
        "completion_ratio": 0 if args.target <= 0 else round(total / args.target, 4),
        "rounds": rounds,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
