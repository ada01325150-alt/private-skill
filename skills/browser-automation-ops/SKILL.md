---
name: browser-automation-ops
description: Use when a task needs local browser automation with `agent-browser`, including page navigation, screenshots, structured element interaction, challenge detection, and compliant human handoff for anti-bot checkpoints.
version: "1.0.0"
---

# Browser Automation Ops

Version: `1.0.0`

## Overview

This skill wraps the local `agent-browser` package into a repeatable operating procedure for browser automation. Use it when you need screenshots, navigation, clicking, form filling, DOM inspection, challenge triage, or guarded handling of slider/image verification checkpoints.

## Use this skill when

- You need to drive a real browser from the terminal.
- You need page screenshots, accessibility snapshots, or structured element refs.
- A site introduces a verification gate and you need to classify it before proceeding.
- A workflow may require dragging a visible slider or pausing for manual verification.

## Do not use this skill when

- The user asks to bypass site security, solve captchas covertly, or exfiltrate cookies/tokens.
- The action is destructive and the user has not explicitly confirmed it.
- The site is untrusted or the account context is unclear.

## Quick start

1. Run the local preflight check:
   - `bash scripts/preflight.sh`
2. Open the target page:
   - `agent-browser open "https://example.com"`
3. Capture state before acting:
   - `agent-browser snapshot -i > /tmp/page-snapshot.txt`
   - `agent-browser screenshot /tmp/page.png`
4. If a challenge is suspected, classify it:
   - `python3 scripts/challenge_triage.py --snapshot-file /tmp/page-snapshot.txt`
5. Re-snapshot after every meaningful page change.

## Workflow

### 1. Baseline capture

Always start with read-only inspection:

- `agent-browser get url`
- `agent-browser get title`
- `agent-browser snapshot -i`
- `agent-browser screenshot --full evidence.png`

### 2. Normal interaction path

Use refs from `snapshot -i`:

- Click buttons: `agent-browser click @e1`
- Fill inputs: `agent-browser fill @e2 "text"`
- Submit safely: `agent-browser press Enter`
- Re-check state: `agent-browser snapshot -i`

### 3. Challenge triage path

If the page contains signs such as `captcha`, `verify`, `drag the slider`, `拼图`, `验证`, or a visually obvious gate:

- Save a fresh snapshot and screenshot.
- Run `scripts/challenge_triage.py`.
- Follow the recommended mode:
  - `slider_exposed`: inspect element boxes and drag only if the control is plainly visible and user intent is legitimate.
  - `image_selection`: stop automated progression and request compliant human help.
  - `manual_review`: preserve evidence and wait for approval or user action.
  - `unknown_gate`: do not guess; collect evidence and escalate.

### 4. Slider handling

For an exposed slider or drag target:

- Use `agent-browser get box <selector-or-ref>` to inspect geometry.
- Use `agent-browser drag <src> <dst>` if both endpoints are accessible.
- Re-snapshot immediately after drag.
- If the page loops back into verification, stop and hand off to the user.

### 5. Session cleanup

- `agent-browser close`
- Remove temporary evidence files if they contain sensitive page data.

## Guardrails

- Never claim to solve a challenge that the page does not expose to the automation surface.
- Never bypass captchas, login walls, or anti-bot systems covertly.
- Prefer evidence capture plus human handoff over brittle automation.
- Treat screenshots, cookies, storage, and page source as sensitive.
- Require explicit confirmation before any purchase, deletion, posting, or account-setting change.

## Resources

- `references/workflow-v1.0.0.md`: full operating notes and decision points.
- `references/test-cases-v1.0.0.md`: test prompts and expected outcomes.
- `scripts/preflight.sh`: verify local prerequisites.
- `scripts/challenge_triage.py`: classify likely verification gates from captured text.
