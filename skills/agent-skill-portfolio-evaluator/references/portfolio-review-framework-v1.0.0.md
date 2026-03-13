# Portfolio Review Framework v1.0.0

Use this file when evaluating how multiple skills behave together for one agent or agent family.

## Core questions

- Which skills own which user intents?
- Where do two skills compete for the same trigger?
- Where does the agent lack a skill for a common task?
- Which skills should hand off to each other?
- Which skills are maintenance overhead without enough value?

## Inventory fields

Capture for each skill:

- name
- purpose
- trigger description
- core workflow
- dependencies
- upstream or downstream skills
- known risks

## Capability matrix axes

Rows can be:

- skills
- workflow stages
- user intents

Columns can be:

- task coverage
- trigger strength
- overlap risk
- handoff quality
- maintenance burden

## Collision patterns

Common problems:

- generic writing skill shadows a domain-specific writing skill
- broad research skill captures tasks meant for a specialist
- helper skill and orchestrator skill both activate on the same request

## Gap patterns

Common problems:

- intake covered, synthesis missing
- analysis covered, delivery missing
- happy path covered, edge-case handoff missing

## Recommended outputs

- inventory table
- capability matrix
- collision list
- gap list
- recommended consolidations
- test plan
