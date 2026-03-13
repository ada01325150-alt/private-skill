# Evaluation Scorecard

## Skill
investor-update-agent

## Version Under Test
0.2.0

## Recommendation
iterate

## Trigger Accuracy
Positive triggers were strong on explicit investor-update requests, but the skill overtriggered on generic update-writing prompts.

## Functional Correctness
The skill consistently produced wins, risks, metrics, and asks. Two runs failed to flag missing metrics before drafting.

## Baseline Comparison
With the skill, output structure was more consistent and required fewer edits than baseline. Baseline was slightly faster.

## A/B Comparison
The revised description reduced false positives compared with the previous version, but one paraphrase still failed to trigger.

## Reliability Notes
Four of five repeated runs passed the core rubric. The main failure mode was missing-data handling.

## Cost / Latency Notes
Slightly higher token use than baseline, but lower human edit distance.

## Top Three Refinements
1. Add a mandatory missing-metrics check before drafting.
2. Tighten the trigger description to exclude generic writing requests.
3. Add one more paraphrased trigger example for weekly stakeholder updates.

## Release Gate Decision
Do not ship yet. Re-run after tightening trigger boundaries and missing-data handling.
