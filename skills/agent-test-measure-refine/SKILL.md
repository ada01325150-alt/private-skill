---
name: agent-test-measure-refine
description: Use when an existing agent skill needs testing, scoring, benchmarking, trigger evaluation, A/B comparison, iterative refinement, or release gating. Best for proving whether a skill works, whether it triggers correctly, and whether edits actually improved it.
version: "1.0.0"
---

# Agent Test Measure Refine

Version: `1.0.0`

## Overview

This skill evaluates and improves existing agent skills.

It follows Anthropic's testing direction:

- test whether the skill triggers when it should
- test whether it performs the workflow correctly
- compare with and without the skill
- compare old and new variants
- refine based on evidence, not intuition alone

Use this skill after creation, after edits, before publishing, and after model or runtime changes.

The deliverable from this skill must be explicit enough that another agent can act on it without guessing what to change next.

## Use this skill when

- A skill already exists and needs evaluation.
- A user asks whether a skill is good, stable, necessary, or better than baseline.
- You need trigger tests, functional tests, or performance comparisons.
- You need a scorecard and concrete improvement actions.
- You need a release gate before publishing or upgrading a skill.

## Do not use this skill when

- The task is to author a skill from scratch with no clear draft.
- The user mainly needs identity design or first-pass workflow creation.

Use `agent-creator` first in those cases.

## Output contract

Always produce these named outputs:

- `evaluation_scorecard`
- `failure_diagnosis`
- `refinement_recommendations`
- `release_decision`

Use `ship`, `iterate`, or `retire` for `release_decision`.

## Evaluation dimensions

Always consider at least these dimensions:

1. `trigger accuracy`
2. `functional correctness`
3. `reliability across repeated runs`
4. `baseline uplift`
5. `cost and latency`
6. `description precision`

Optional dimensions:

- safety and boundaries
- adversarial robustness
- tool-call quality
- human-edit distance

## Quick start

1. Identify the current version under test.
2. Build or load a test set.
3. Run baseline without the skill.
4. Run the same tasks with the skill.
5. If comparing revisions, run blinded A/B comparisons.
6. Score results with a rubric.
7. Propose the smallest changes likely to improve outcomes.
8. If helpful, format the report with `scripts/render_scorecard.py`.
9. Re-test before recommending release.

## Workflow

### 1. Define the test set

Build a compact but representative set containing:

- obvious trigger cases
- paraphrased trigger cases
- negative trigger cases
- core functional tasks
- edge cases
- adversarial or stress cases

Start with a small but sharp set. Expand only after the skill fails or stabilizes.

### 2. Separate three kinds of tests

#### Trigger tests

Check whether the skill loads when it should, and stays out when it should not.

#### Functional tests

Check whether the skill completes the intended workflow correctly.

#### Comparative tests

Check whether the skill is actually better than:

- no skill
- previous version
- alternative description or workflow

### 3. Run repeated trials

Do not trust a single run.

For non-deterministic tasks, run multiple times and note:

- pass rate
- failure shape
- consistency
- average cost or latency if available

### 4. Score with behavior, not string matching alone

Prefer rubrics and behavioral invariants over exact output equality.

Examples:

- did the skill ask the right clarifying question
- did it avoid forbidden claims
- did it produce all required sections
- did it use tools correctly

### 5. Diagnose the failure source

Classify failures into:

- undertriggering
- overtriggering
- weak workflow steps
- poor identity or boundary definition
- missing examples
- excessive verbosity
- model drift or infra drift

### 6. Refine minimally

Prefer small changes first:

- tighten the description
- add or sharpen trigger examples
- clarify a workflow step
- strengthen a boundary
- move detail from `SKILL.md` into `references/`

Avoid rewriting everything after one bad run.

### 7. Release gate

Only recommend release when:

- trigger tests are acceptable
- functional tests pass at the agreed threshold
- the skill beats or justifies itself versus baseline
- no serious regression is introduced

If the baseline already matches or exceeds the skill on the target task, say so explicitly and consider `retire`.

## Anti-patterns

- single-run conclusions
- happy-path-only testing
- exact-string scoring for open-ended tasks
- changing too many variables at once
- claiming improvement without baseline comparison

## Resources

- `references/eval-framework-v1.0.0.md` for test design and scoring.
- `references/comparison-rules-v1.0.0.md` for baseline rules, repeated trials, and retirement decisions.
- `references/scorecard-v1.0.0.md` for reporting format.
- `assets/testcase-template.yaml` for starter eval cases.
- `assets/testcase-template.json` for script-friendly eval cases.
- `assets/scorecard-template.md` for final output.
- `assets/example-scorecard.md` for a realistic filled report.
- `assets/scorecard-input-example.json` for script-friendly result input.
- `scripts/render_scorecard.py` to normalize structured evaluation results into Markdown.
