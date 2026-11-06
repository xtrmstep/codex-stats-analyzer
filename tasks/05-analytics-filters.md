# 05 — Shared analytics and global filter contract

Status: Not started | Phase: 1 | Dependencies: 03, 04

Specification: §§3.3, 6.1–6.3.

## Scope

- Build reusable pandas analytics over normalized increments; keep metric logic independent of Streamlit rendering.
- Support date, project, model, session and agent-role filters now, with a defined integration path for labels, task type and execution mode in Phase 2.
- Define timezone handling, daily/weekly/monthly buckets, filter intersection and empty/missing-value behavior.
- Provide tokens, input/output distribution, cache percentage, distinct sessions/agents, subagent share, and grouping by project/model/session. Add run and label aggregation in task 10.
- Specify how agent filters affect hierarchy context and totals, and how overlapping runs or multiple labels avoid duplicating global usage.
- Carry observed/manual/estimated provenance and completeness through aggregate results.

## Acceptance and validation

- Deterministic fixtures verify cross-filter intersections, bucket boundaries, distinct counts, weighted cache ratios, unknown values and empty results.
- Every consuming view uses this shared contract; no chart maintains a separate conflicting total calculation.
