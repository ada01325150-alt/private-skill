#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


SECTIONS = [
    ("Skill", "skill_name"),
    ("Version Under Test", "version_under_test"),
    ("Recommendation", "recommendation"),
    ("Trigger Accuracy", "trigger_accuracy"),
    ("Functional Correctness", "functional_correctness"),
    ("Baseline Comparison", "baseline_comparison"),
    ("A/B Comparison", "ab_comparison"),
    ("Reliability Notes", "reliability_notes"),
    ("Cost / Latency Notes", "cost_latency_notes"),
    ("Top Three Refinements", "top_three_refinements"),
    ("Release Gate Decision", "release_gate_decision"),
]


def render_value(value) -> list[str]:
    if isinstance(value, list):
        return [f"- {entry}" for entry in value] if value else ["- None provided"]
    if value in (None, ""):
        return ["- None provided"]
    return [str(value)]


def render_scorecard(result: dict) -> str:
    lines = ["# Evaluation Scorecard", ""]
    for title, key in SECTIONS:
        lines.append(f"## {title}")
        lines.extend(render_value(result.get(key)))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a normalized evaluation scorecard from JSON.")
    parser.add_argument("result", help="Path to a JSON file following scorecard-input-example.json")
    parser.add_argument("--out", help="Optional output Markdown path")
    args = parser.parse_args()

    result = json.loads(Path(args.result).read_text())
    output = render_scorecard(result)
    if args.out:
        Path(args.out).write_text(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
