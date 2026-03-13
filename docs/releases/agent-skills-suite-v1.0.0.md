# Agent Skills Suite

Version: `1.0.0`

## Output root

`/Users/mm0000/Documents/private-skill`

## Included packages

- `skills/agent-skill-portfolio-evaluator/`
  - Evaluates and optimizes the related skill set attached to an agent, including collisions, gaps, and portfolio-level tests.
- `skills/agent-architecture-evaluator/`
  - Evaluates and optimizes agent or multi-agent architectures, including routing, memory, coordination, and observability.
- `skills/agent-creator/`
  - Creates first-pass agent skills with identity, trigger contracts, file plans, and starter eval sets.
  - Includes references, templates, examples, and a deterministic bundle renderer.
- `skills/agent-test-measure-refine/`
  - Tests, benchmarks, scores, and refines existing agent skills.
  - Includes comparison guidance, scorecard templates, examples, and a deterministic scorecard renderer.
- `scripts/validate_skills.py`
  - Validates skill structure, metadata, cross-links, and Python helper syntax for local skills.

## Source basis

- Anthropic PDF: `The Complete Guide to Building Skills for Claude`
- Anthropic blog: `Improving skill-creator: Test, measure, and refine Agent Skills`
- Local skill reference: `/Users/mm0000/.codex/skills/.system/skill-creator/SKILL.md`

## ClawHub publish copy

- `skills/agent-skill-portfolio-evaluator/assets/clawhub-publish.md`
  - Canonical name, slug, short description, marketplace one-liner, long description, changelog, and example publish command.
- `skills/agent-architecture-evaluator/assets/clawhub-publish.md`
  - Canonical name, slug, short description, marketplace one-liner, long description, changelog, and example publish command.

## Validation status

- `python3 scripts/validate_skills.py` passes for:
  - `skills/agent-creator`
  - `skills/agent-test-measure-refine`
  - `skills/browser-automation-ops`
  - `skills/wxgzh-search`

## Versioning note

All new Markdown, YAML, JSON, and Python files created for this delivery include explicit `1.0.0`-level package intent or are tied to the `v1.0.0` delivery set.
