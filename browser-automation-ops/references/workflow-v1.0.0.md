# Browser Automation Ops Workflow

Version: `1.0.0`

## Purpose

Turn the local `agent-browser` installation into a safe, repeatable browser automation workflow with explicit challenge triage.

## Decision tree

1. Need read-only evidence only:
   - Use `open`, `snapshot`, `get`, `screenshot`.
2. Need normal interaction:
   - Use `click`, `fill`, `press`, `select`, `drag`, then re-snapshot.
3. Need to understand a verification checkpoint:
   - Capture snapshot and screenshot, then run `scripts/challenge_triage.py`.
4. Need to complete a challenge that requires hidden reasoning or image matching:
   - Stop automation and request human verification.

## Standard command pattern

```bash
agent-browser open "https://example.com"
agent-browser snapshot -i > /tmp/page-snapshot.txt
agent-browser screenshot /tmp/page.png
python3 scripts/challenge_triage.py --snapshot-file /tmp/page-snapshot.txt
```

## Challenge classes

- `slider_exposed`: visible drag control or slider language is present.
- `image_selection`: click-the-image / rotate-the-object / match-the-picture pattern.
- `manual_review`: SMS, QR login, OTP, or explicit human confirmation.
- `unknown_gate`: challenge signals exist but classification is weak.

## Recommended responses

- `slider_exposed`: inspect coordinates, drag once, and verify outcome.
- `image_selection`: preserve evidence and pause.
- `manual_review`: pause and request user action.
- `unknown_gate`: do not improvise; gather evidence and stop.

## Evidence checklist

- Current URL
- Page title
- Interactive snapshot
- Full-page screenshot
- Any visible challenge text
- Result after attempted interaction
