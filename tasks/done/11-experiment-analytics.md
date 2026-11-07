# 11 — Experiment groups and comparison metrics

Status: Complete; independent review passed | Phase: 3 | Dependencies: 05, 08, 09

Specification: §§2.5, 7.1–7.3; MVP 8, 13.

## Scope

Review: independent Astra review passed at `99c2c76`, including eligibility, cache ratios, overlaps, outcomes and baseline differences.

- Define two or more named groups through reusable run filters and labels. Specify interaction with global filters and flag runs shared across groups.
- Compute sample size, mean/median tokens, cache percentage, output tokens, subagent share, elapsed time, success rate and optional evaluation score.
- Specify eligible denominators and report coverage for missing outcomes, scores, durations or token fields. Unknown outcomes must not silently count as failures.
- Define a baseline or explicit pairwise comparison policy. For token and duration metrics show absolute and percentage differences, with zero/missing baselines handled without misleading percentages.
- Supply distribution data and flag differences in task types, models and other relevant recorded conditions.
- Report descriptive differences without causal claims; do not invent quality scores or verified durations.

## Acceptance and validation

- Hand-calculated groups verify every metric and difference, including empty/singleton groups, missing data, mixed conditions, group overlap and zero baselines.
- Run counts and eligible-value counts remain visible and agree with filtered source runs.

## Decisions and validation evidence

- Named group filters intersect global filters. The first group is baseline; runs can appear in multiple groups and overlaps are reported. Missing-source runs remain in unfiltered groups with unknown measures, but cannot match filters requiring observed event attributes. Token results are root-thread-only and partial/estimated. Per-run distributions preserve IDs; no causal conclusion is inferred.
- Every measure reports eligible and total run counts. Mean/median tokens and mean output use known run values. Cache percentage is weighted from paired cached/input increment values in eligible runs with positive input. Duration uses full-run observed/manual spans only when the global/group filters retain all run events; these spans are not verified execution durations. Success rate excludes unknown and partial outcomes from the success/failure denominator. Scores use entered values only; subagent share remains unknown. Differences for mean/median/output tokens and elapsed time use baseline absolute and percentage change; missing or zero baseline leaves percentage unknown.
- Condition flags compare effective task type, execution mode and observed models, including unknown values. Inline synthetic checks passed hand-calculated means/median, output, weighted cache, outcome/score eligibility, missing and empty groups, overlap, baseline differences, zero baseline, and paired partial cache inputs. Python compilation passed; independent review pending.

