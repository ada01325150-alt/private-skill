# Trigger Design v1.0.0

Use this file when drafting or reviewing the trigger surface for a new skill.

## Classification first

Before writing the description, classify the skill:

- `capability uplift` — the skill teaches the model techniques or workflows that improve base capability.
- `encoded preference` — the skill codifies how a team wants work done.
- `hybrid` — both are materially true.

This affects what the evaluator should later prove.

## Trigger writing rules

Every description should answer three questions:

1. What job does the skill do?
2. When should it activate?
3. What nearby requests should it leave alone?

Good triggers name the workflow, user intent, and rough scope.

Bad triggers overuse generic language like:

- help the user
- improve output
- assist with tasks
- handle writing

## Positive / negative pattern set

Always draft:

- `3–5` obvious trigger examples
- `3–5` paraphrased trigger examples
- `3–5` non-trigger examples

If you cannot write strong negatives, the skill boundary is still too fuzzy.

## File-plan patterns

### Small skill

- `SKILL.md`
- `agents/openai.yaml`
- `references/<one focused file>.md`
- optional `assets/<one template>.md`

### Medium skill

- `SKILL.md`
- `agents/openai.yaml`
- `references/identity-or-rubric.md`
- `references/workflow-or-eval.md`
- `assets/template-or-example.md`
- optional `scripts/<one deterministic helper>.py`

## Review checklist

- Could a nearby but unrelated request trigger this by accident?
- Would a paraphrase still activate it?
- Does the description say what it does not cover?
- Is any important nuance hidden only in a reference file?

If yes, move the core boundary back into `SKILL.md`.
