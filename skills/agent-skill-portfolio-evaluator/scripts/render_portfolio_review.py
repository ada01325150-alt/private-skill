#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, List, Tuple

SECTIONS: List[Tuple[str, str]] = [
    ("portfolio_inventory", "portfolio_inventory"),
    ("capability_matrix", "capability_matrix"),
    ("collision_and_gap_report", "collision_and_gap_report"),
    ("portfolio_test_plan", "portfolio_test_plan"),
    ("optimization_backlog", "optimization_backlog"),
    ("portfolio_release_recommendation", "portfolio_release_recommendation"),
]


def render_value(value: Any) -> List[str]:
    if isinstance(value, list):
        return [f"- {item}" for item in value] if value else ["- None provided"]
    if value in (None, ""):
        return ["- None provided"]
    return [str(value)]


def render_review(data: dict) -> str:
    lines = ["# Portfolio Review", ""]
    for title, key in SECTIONS:
        lines.append(f"## {title}")
        lines.extend(render_value(data.get(key)))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a portfolio review from JSON.")
    parser.add_argument("input", help="Path to JSON input")
    parser.add_argument("--out", help="Optional Markdown output path")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    output = render_review(data)
    if args.out:
        Path(args.out).write_text(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
