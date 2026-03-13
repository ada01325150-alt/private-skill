# Example Agent Brief

## Goal
Create a skill that turns weekly operating notes into a concise founder update for investors.

## Primary User
Seed-stage founder who sends a weekly update every Friday.

## Repeated Workflow
Collect notes, normalize metrics, summarize wins and risks, draft a consistent investor-facing update.

## Inputs
- rough notes
- KPI snapshot
- pending asks

## Outputs
- short investor update
- optional internal follow-up checklist

## Tools or Integrations
- none required for v1

## Boundaries
- must not invent metrics
- must separate facts from interpretation
- must flag missing numbers before finalizing

## Failure Modes
- over-polished but vague writing
- missing downside risks
- accidental hallucinated metrics

## Success Criteria
- concise and credible update
- consistent structure week to week
- explicit missing-data handling

## Seed Eval Notes
Later evaluation should compare this skill against a plain prompt to see whether it reduces edit distance and improves consistency.
