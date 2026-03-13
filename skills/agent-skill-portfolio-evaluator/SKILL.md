---
name: agent-skill-portfolio-evaluator
description: Use when evaluating, testing, and optimizing the set of skills attached to an agent or agent family. Best for detecting overlap, trigger collisions, missing coverage, weak sequencing, and skill portfolio drift.
version: "1.0.0"
---

# Agent Skill Portfolio Evaluator

Version: `1.0.0`

## Overview

This skill reviews an agent's related skill set as a portfolio, not as isolated skills.

Use it when the problem is not “is this single skill good?” but “does this collection of skills work well together for the agent that depends on them?”

It is designed for:

- skill overlap analysis
- trigger collision review
- capability coverage mapping
- sequencing and dependency assessment
- portfolio-level test and optimization planning

## Use this skill when

- An agent relies on multiple skills and you need to review them together.
- Different skills may overlap, conflict, or leave important gaps.
- A team wants to simplify or strengthen an agent’s skill stack.
- You need a coverage map, collision analysis, and optimization backlog.

## Do not use this skill when

- You are creating a new skill from scratch.
- You only need to evaluate one existing skill in isolation.
- The main issue is agent runtime architecture rather than the skill portfolio.

Use `agent-creator`, `agent-test-measure-refine`, or `agent-architecture-evaluator` in those cases.

## Output contract

Always produce these named outputs:

- `portfolio_inventory`
- `capability_matrix`
- `collision_and_gap_report`
- `portfolio_test_plan`
- `optimization_backlog`
- `portfolio_release_recommendation`

## Review dimensions

Evaluate at least these dimensions:

1. `coverage completeness`
2. `trigger separation`
3. `workflow sequencing`
4. `redundancy or bloat`
5. `handoff quality between skills`
6. `portfolio maintainability`

## Quick start

1. Enumerate the skills used by the agent.
2. Map each skill to jobs-to-be-done.
3. Identify overlapping triggers and duplicated logic.
4. Identify missing capability zones.
5. Design a portfolio-level test set.
6. Prioritize the smallest high-value optimizations.

## Workflow

### 1. Build the inventory

For each skill, capture:

- purpose
- trigger surface
- main workflow
- dependencies
- likely overlap neighbors

### 2. Build a capability matrix

Map skills against:

- user intents
- workflow stages
- tool or integration requirements
- escalation paths

See `references/portfolio-review-framework-v1.0.0.md`.

### 3. Check trigger collisions

Look for:

- two skills that activate on the same intent
- generic descriptions that absorb specialized requests
- skills that should cooperate but compete instead

### 4. Check coverage gaps

Look for:

- common user intents with no clear skill owner
- workflow stages with no support skill
- unsafe fallback behavior when no skill triggers

### 5. Test the portfolio

Design tests for:

- obvious routing
- paraphrased routing
- ambiguous routing
- multi-step workflows that require two or more skills
- failure handoff behavior

### 6. Optimize the portfolio

Prefer these changes first:

- tighten trigger descriptions
- retire duplicated skills
- split over-broad skills
- merge low-value fragments
- document ordering or handoff rules

## Anti-patterns

- reviewing skills only one by one
- ignoring cross-skill collisions
- adding new skills before removing duplication
- treating more skills as automatically better

## Resources

- `references/portfolio-review-framework-v1.0.0.md` for the review method.
- `references/scoring-model-v1.0.0.md` for prioritization and release decisions.
- `assets/capability-matrix-template.md` for mapping skills to intents and stages.
- `assets/example-portfolio-review.md` for a filled review.
- `assets/portfolio-input-example.json` for structured input.
- `scripts/render_portfolio_review.py` to normalize a structured review into Markdown.
