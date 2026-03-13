# Eval Framework v1.0.0

Use this file when designing or reviewing evaluations for an existing agent skill.

## Core principles

- Evaluate behavior, not formatting accidents.
- Use repeated trials for non-deterministic tasks.
- Compare against a baseline whenever possible.
- Keep trigger tests separate from functional tests.
- Treat regressions as first-class failures.

## Recommended test layers

### 1. Trigger tests

Create:

- obvious positives
- paraphrased positives
- obvious negatives
- adjacent negatives

Measure:

- false positives
- false negatives

### 2. Functional tests

Check:

- required outputs present
- workflow steps followed
- tool usage correct
- edge cases handled
- constraints obeyed

### 3. Comparative tests

Run:

- `without skill`
- `with skill`
- `old version vs new version`

Measure:

- task quality
- consistency
- token cost if available
- elapsed time if available
- human correction burden

### 4. Adversarial tests

Stress the skill with:

- ambiguous phrasing
- distracting irrelevant instructions
- partial inputs
- conflicting constraints
- unsafe or out-of-scope requests

## Scoring guidance

Prefer a rubric with `0–3` or `0–5` scoring on a few stable dimensions.

Example dimensions:

- trigger correctness
- task completion
- boundary adherence
- clarity
- efficiency

If you need machine-friendly formatting for the final report, `scripts/render_scorecard.py` accepts a JSON result object and renders a normalized Markdown scorecard.

## Failure diagnosis map

- triggers miss paraphrases → widen description with examples
- triggers on unrelated work → narrow scope and add negatives
- correct workflow but poor tone → revise identity or anti-voice
- frequent partial completion → split workflow into explicit steps
- strong output but no uplift over baseline → question whether the skill is still necessary
