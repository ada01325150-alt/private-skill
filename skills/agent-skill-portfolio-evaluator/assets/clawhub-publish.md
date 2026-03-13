# ClawHub Publish Copy

## Canonical name
Agent Skill Portfolio Evaluator

## Recommended slug
agent-skill-portfolio-evaluator

## Short description
Evaluate and optimize the full skill portfolio attached to an agent.

## Marketplace one-liner
Review an agent's related skills as a portfolio to detect overlap, trigger collisions, missing coverage, weak handoffs, and portfolio drift.

## Long description
Use this skill when an agent depends on multiple related skills and the real question is whether the full skill portfolio works well together.

It evaluates the portfolio as a system rather than reviewing each skill in isolation. It helps identify duplicated responsibilities, trigger collisions, weak sequencing, missing capability coverage, and unclear handoff behavior across skills.

This skill is useful for teams maintaining specialist skill stacks, orchestrator-plus-helper setups, or evolving agent families where skills have accumulated over time.

Typical outputs include a portfolio inventory, capability matrix, collision and gap report, portfolio-level test plan, optimization backlog, and a release recommendation.

## Recommended positioning
Best for reviewing the quality of an agent's related skill stack, not for testing one skill in isolation and not for reviewing runtime architecture.

## Suggested changelog
Initial release. Adds portfolio-level evaluation for agent skill stacks, including collision analysis, coverage mapping, handoff review, portfolio test planning, and optimization prioritization.

## Example publish command
clawhub publish ./skills/agent-skill-portfolio-evaluator --slug agent-skill-portfolio-evaluator --name "Agent Skill Portfolio Evaluator" --version 1.0.0 --changelog "Initial release. Adds portfolio-level evaluation for agent skill stacks, including collision analysis, coverage mapping, handoff review, portfolio test planning, and optimization prioritization."
