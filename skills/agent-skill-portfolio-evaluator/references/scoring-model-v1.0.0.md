# Scoring Model v1.0.0

Use this file to rank portfolio-level optimization work.

## Score dimensions

Use a simple `1–5` scale for:

- `impact on user success`
- `collision severity`
- `coverage importance`
- `maintenance cost`
- `ease of fix`

## Prioritization rules

Prioritize first:

1. high-severity trigger collisions
2. gaps in common or high-risk workflows
3. duplicated skills with low differentiation
4. unclear handoffs in multi-step flows

## Release recommendation values

Use one of:

- `stable` — portfolio is coherent enough for normal use
- `iterate` — portfolio works but collisions or gaps remain
- `restructure` — portfolio shape is wrong and needs consolidation or redesign
