# Scorecard v1.0.0

Use this format when handing evaluation results back to the user.

If you need a deterministic formatter, use `scripts/render_scorecard.py` with a JSON object matching the section names below.

## Summary

- skill name
- version under test
- evaluator date
- recommendation: `ship`, `iterate`, or `retire`

## Trigger results

- positive coverage
- negative precision
- notable false positives
- notable false negatives

## Functional results

- passed scenarios
- failed scenarios
- recurring failure mode

## Comparison

- baseline vs skill
- old vs new
- observed uplift or regression

## Stability

- repeated-run consistency
- flaky cases

## Cost and latency

- notable changes if available

## Recommended refinements

List the smallest changes first.

## Release decision

State:

- what is safe to ship now
- what must be fixed before release
- what should be monitored after release

Allowed values:

- `ship`
- `iterate`
- `retire`
