#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

PATTERNS: List[Tuple[str, str]] = [
    (r"drag the slider|slider verification|slide to verify|拖动滑块|按住滑块|滑块验证", "slider_exposed"),
    (r"select all images|click the matching image|rotate the object|拼图|找出.*图片|点击.*图片|图中", "image_selection"),
    (r"scan qr|qr code|sms code|otp|two-factor|人工审核|人工验证|短信验证码", "manual_review"),
    (r"captcha|verify you are human|robot check|安全验证|人机验证|异常访问", "unknown_gate"),
]


def load_text(snapshot_file: str, text: str) -> str:
    if text:
        return text
    if snapshot_file:
        return Path(snapshot_file).read_text(encoding="utf-8")
    return ""


def classify(text: str) -> Dict[str, object]:
    normalized = text.lower()
    matches = []
    scores = {"slider_exposed": 0, "image_selection": 0, "manual_review": 0, "unknown_gate": 0}

    for pattern, label in PATTERNS:
        for found in re.findall(pattern, normalized, flags=re.IGNORECASE):
            matches.append({"label": label, "signal": found})
            scores[label] += 1

    label = max(scores, key=scores.get)
    if scores[label] == 0:
        label = "no_gate_detected"

    actions = {
        "slider_exposed": [
            "Capture a screenshot and inspect element boxes before dragging.",
            "Attempt one explicit drag only if the slider is visible and user intent is legitimate.",
            "Re-snapshot immediately after drag.",
        ],
        "image_selection": [
            "Do not guess the image answer.",
            "Preserve screenshot evidence and request manual help.",
            "Resume automation only after the user confirms the page is clear.",
        ],
        "manual_review": [
            "Pause automation.",
            "Ask the user to complete the verification step directly.",
            "Continue only after confirmation.",
        ],
        "unknown_gate": [
            "Collect URL, title, snapshot, and screenshot.",
            "Do not improvise a bypass.",
            "Escalate to the user with the captured evidence.",
        ],
        "no_gate_detected": [
            "No strong challenge signal was detected in the provided text.",
            "If the UI still looks blocked, take a screenshot and review manually.",
        ],
    }

    return {
        "challenge_type": label,
        "scores": scores,
        "matched_signals": matches,
        "recommended_actions": actions[label],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify likely verification gates from browser snapshot text.")
    parser.add_argument("--snapshot-file", default="", help="path to a text snapshot captured from agent-browser")
    parser.add_argument("--text", default="", help="raw challenge text")
    args = parser.parse_args()

    text = load_text(args.snapshot_file, args.text)
    result = classify(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
