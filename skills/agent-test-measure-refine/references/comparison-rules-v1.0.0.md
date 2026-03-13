# Comparison Rules v1.0.0

Use this file when deciding whether a skill is better than baseline or still worth keeping.

## Baseline first

When possible, run the same task:

- without the skill
- with the current skill
- with the revised skill if one exists

Do not claim an improvement without a comparable baseline.

## Repeated trials

For non-deterministic tasks, do more than one run.

At minimum, note:

- total runs
- pass count
- recurring failure modes
- whether failures cluster around one test type

## When to prefer `iterate`

Choose `iterate` when:

- trigger accuracy is mixed but fixable
- the skill helps, but regressions are present
- the workflow is right but phrasing or boundaries need work

## When to prefer `ship`

Choose `ship` when:

- trigger behavior is acceptable
- core functional tests pass reliably enough for the target use
- the skill beats baseline or clearly reduces human correction burden

## When to prefer `retire`

Choose `retire` when:

- baseline consistently matches or beats the skill
- the skill adds complexity without measurable benefit
- the skill causes persistent overtriggering or unsafe behavior that outweighs its value

Retirement is especially relevant for capability-uplift skills as models improve.
