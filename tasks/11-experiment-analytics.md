# 11 — Experiment groups and comparison metrics

Status: Not started | Phase: 3 | Dependencies: 05, 08, 09

Specification: §§2.5, 7.1–7.3; MVP 8, 13.

## Scope

- Define two or more named groups through reusable run filters and labels. Specify interaction with global filters and flag runs shared across groups.
- Compute sample size, mean/median tokens, cache percentage, output tokens, subagent share, elapsed time, success rate and optional evaluation score.
- Specify eligible denominators and report coverage for missing outcomes, scores, durations or token fields. Unknown outcomes must not silently count as failures.
- Define a baseline or explicit pairwise comparison policy. For token and duration metrics show absolute and percentage differences, with zero/missing baselines handled without misleading percentages.
- Supply distribution data and flag differences in task types, models and other relevant recorded conditions.
- Report descriptive differences without causal claims; do not invent quality scores or verified durations.

## Acceptance and validation

- Hand-calculated groups verify every metric and difference, including empty/singleton groups, missing data, mixed conditions, group overlap and zero baselines.
- Run counts and eligible-value counts remain visible and agree with filtered source runs.
