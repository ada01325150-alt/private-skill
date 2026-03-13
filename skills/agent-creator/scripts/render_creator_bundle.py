#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def section(title: str, value, lines: list[str]) -> None:
    lines.append(f"## {title}")
    if isinstance(value, dict):
        if not value:
            lines.append("- None provided")
        for key, item in value.items():
            lines.append(f"### {key}")
            if isinstance(item, list):
                for entry in item:
                    lines.append(f"- {entry}")
            else:
                lines.append(str(item))
    elif isinstance(value, list):
        if not value:
            lines.append("- None provided")
        for entry in value:
            lines.append(f"- {entry}")
    elif value in (None, ""):
        lines.append("- None provided")
    else:
        lines.append(str(value))
    lines.append("")


def render_bundle(spec: dict) -> str:
    lines: list[str] = [f"# Creator Bundle: {spec.get('skill_name', 'unnamed-skill')}", ""]
    ordered_keys = [
        "classification",
        "agent_brief",
        "identity_spec",
        "trigger_contract",
        "file_plan",
        "seed_eval_set",
        "evaluator_handoff",
    ]
    for key in ordered_keys:
        section(key, spec.get(key), lines)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a normalized creator handoff bundle from JSON.")
    parser.add_argument("spec", help="Path to a JSON file following creator-spec-example.json")
    parser.add_argument("--out", help="Optional output Markdown path")
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text())
    output = render_bundle(spec)
    if args.out:
        Path(args.out).write_text(output)
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
