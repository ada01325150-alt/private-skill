# Output Contract v1.0.0

Every run of `agent-creator` should produce these sections in order.

If you need machine-friendly formatting for handoff, `scripts/render_creator_bundle.py` accepts a JSON object matching the same section names and renders a normalized Markdown bundle.

## 1. Skill classification

- `capability uplift`
- `encoded preference`
- `hybrid`

Include one sentence explaining why.

## 2. Agent brief

- user
- problem
- repeated workflow
- desired outcome
- key constraints
- failure risks

## 3. Identity spec

If the skill is agent-like, include:

- purpose
- values
- perspective
- voice
- anti-voice
- boundaries

## 4. Trigger contract

List:

- `should_trigger`
- `should_not_trigger`
- likely paraphrases
- likely false-positive cases

## 5. File plan

List the files to create and why each exists.

## 6. Seed eval set

Minimum:

- 3 positive trigger prompts
- 3 negative trigger prompts
- 3 functional test prompts
- 1 edge case
- 1 baseline comparison prompt

## 7. Handoff note

Give `agent-test-measure-refine`:

- what success looks like
- what may regress
- what is unproven
- what should be benchmarked first

## Suggested JSON keys for script-assisted output

```json
{
  "skill_name": "example-skill",
  "classification": "encoded preference",
  "agent_brief": {},
  "identity_spec": {},
  "trigger_contract": {},
  "file_plan": [],
  "seed_eval_set": {},
  "evaluator_handoff": {}
}
```

The script should only normalize the structure; the skill still owns the judgment.
