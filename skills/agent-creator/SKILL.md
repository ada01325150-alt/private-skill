---
name: agent-creator
description: Use when a user wants to create a new agent skill or define a new agent identity, workflow, trigger description, and initial evaluation set. Best for first-pass agent creation, skill scaffolding, and turning rough workflow ideas into a portable skill package.
version: "1.0.0"
---

# Agent Creator

Version: `1.0.0`

## Overview

This skill creates the first reliable version of an agent or agent skill.

It follows three constraints:

- Anthropic's skill design guidance: progressive disclosure, composability, and portability.
- Anthropic's newer `test / measure / refine` direction: every created skill should ship with explicit success criteria and seed eval cases.
- Local `skill-creator` conventions: keep `SKILL.md` lean, move detail into `references/` and `assets/`, and generate reusable bundled outputs instead of one-off prose.

Use this skill to turn a rough idea into a publishable starting point, not to prove the skill is production-ready.

The deliverable from this skill must be consumable by `agent-test-measure-refine` without further interpretation.

## Use this skill when

- A user wants to create a new agent or agent skill.
- A user has a workflow, persona, or use case but no structured skill package yet.
- You need to define identity, trigger boundaries, workflow steps, and output contracts.
- You need a first-pass `SKILL.md` plus starter eval cases for later testing.

## Do not use this skill when

- The main task is to benchmark, score, compare, or optimize an existing skill.
- The user already has a skill and wants regression checks or A/B comparisons.
- The task is mostly about runtime telemetry, production incident review, or statistical evaluation.

Use `agent-test-measure-refine` for those cases.

## Handoff contract

Always hand off these named outputs:

- `agent_brief`
- `identity_spec`
- `trigger_contract`
- `file_plan`
- `seed_eval_set`
- `evaluator_handoff`

If one is missing, the creation run is incomplete.

## Outputs

Produce a compact package with these parts:

1. `agent brief` — purpose, user, domain, key tasks, boundaries.
2. `identity spec` — purpose, values, perspective, voice, anti-voice, escalation style.
3. `skill scaffold` — `SKILL.md` with frontmatter, workflow, guardrails, and references.
4. `metadata scaffold` — `agents/openai.yaml` with a clear trigger description.
5. `seed eval set` — a small set of trigger tests, functional tests, and baseline comparison prompts.
6. `handoff note` — what the evaluator skill should test next.

## Quick start

1. Classify the skill:
   - `capability uplift`
   - `encoded preference`
   - `hybrid`
2. Capture the agent's identity triad using `references/identity-spec-v1.0.0.md`.
3. Define the trigger surface:
   - what should trigger
   - what should not trigger
4. Draft the minimal `SKILL.md`.
5. Generate a seed eval set using `references/output-contract-v1.0.0.md`.
6. If helpful, format the output with `scripts/render_creator_bundle.py`.
7. Hand off to `agent-test-measure-refine`.

## Workflow

### 1. Clarify the job to be done

Extract:

- target user
- repeated workflow
- expected outcome
- required tools or files
- failure modes

If the workflow is vague, ask for one representative task and one failure example before drafting the skill.

### 2. Define identity before instructions

For agent-like skills, define identity first, because tone and boundary mistakes often come from a weak identity layer.

Use the identity triad:

- `purpose`
- `values`
- `perspective`

Then define:

- `voice behaviors`
- `anti-voice`
- `boundary tiers`
- `adaptation rules`

See `references/identity-spec-v1.0.0.md`.

### 3. Write a narrow trigger description

Descriptions should be specific enough to avoid false positives and broad enough to catch paraphrases.

Always include:

- what the skill is for
- when it should be used
- adjacent cases it should not absorb

Do not rely on vague phrases like `help with writing`, `assist with tasks`, or `improve output`.

See `references/trigger-design-v1.0.0.md`.

### 4. Build the minimal skill package

Create only the files that directly help the agent do the job:

- `SKILL.md`
- `agents/openai.yaml`
- optional `references/`
- optional `assets/`
- optional `scripts/` only when deterministic execution matters

Prefer concise procedural guidance over exhaustive explanation.

### 5. Seed evals at creation time

Every newly created skill should include a small initial eval set:

- `3–5` trigger positives
- `3–5` trigger negatives
- `3–5` functional tests
- `1–3` edge or adversarial tests
- `1–3` baseline comparison prompts

Do not claim quality from these alone; they exist to bootstrap later measurement.

When useful, emit the eval seed in both prose and machine-friendly JSON using the example shapes in `assets/creator-spec-example.json`.

### 6. Handoff cleanly

End with a handoff note for `agent-test-measure-refine` covering:

- intended use cases
- risky failure modes
- uncertain trigger boundaries
- metrics to optimize

## Guardrails

- Do not turn a vague idea into a bloated skill. Start small.
- Do not write long narrative docs outside the skill package.
- Do not skip eval seeding.
- Do not use a generic identity if the user is clearly asking for an opinionated agent.
- Do not overfit to one anecdotal example.

## Resources

- `references/identity-spec-v1.0.0.md` for identity and persona design.
- `references/trigger-design-v1.0.0.md` for trigger writing, classification, and file-plan patterns.
- `references/output-contract-v1.0.0.md` for required deliverables and seed evals.
- `assets/agent-brief-template.md` for a starter brief format.
- `assets/creator-output-template.md` for a complete handoff structure.
- `assets/example-agent-brief.md` for a realistic example.
- `assets/creator-spec-example.json` for script-friendly structured input.
- `scripts/render_creator_bundle.py` to format a JSON spec into a normalized handoff bundle.
