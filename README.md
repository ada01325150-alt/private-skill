# private-skill

A small private repository of reusable Codex/OpenClaw-style skills.

## Repository layout

- `skills/browser-automation-ops`
  - Local browser automation workflow built around `agent-browser`
  - Includes guarded challenge triage and preflight checks
- `skills/wxgzh-search`
  - WeChat public article discovery and harvest workflow
  - Includes keyword search, queue harvest, direct URL reading, and synthesis helpers
- `docs/releases/task-1.0.0-v1.0.0.md`
  - Delivery note for the `task 1.0.0` package

## Skill inventory

| Skill | Purpose | Entry file |
|---|---|---|
| `browser-automation-ops` | Browser automation, screenshots, structured interaction, challenge triage | `skills/browser-automation-ops/SKILL.md` |
| `wxgzh-search` | WeChat article search, harvest, direct-read fallback, synthesis | `skills/wxgzh-search/SKILL.md` |

## Usage notes

- Each skill is self-contained in its own folder.
- `SKILL.md` is the main entry point for skill behavior.
- `agents/openai.yaml` contains UI-facing metadata.
- `scripts/` contains reusable helpers and wrappers.
- `references/` contains supporting operating guidance.

## Versioning

- Current delivery baseline: `v1.0.0`
- Initial contents were generated from `task 1.0.0` on 2026-03-09.
