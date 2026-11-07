# 05 — Shared analytics and global filter contract

Status: Complete; independent review passed | Phase: 1 | Dependencies: 03, 04

Specification: §§3.3, 6.1–6.3.

## Scope

Review: independent Astra re-review passed at `357acd8`; observed-entity counting and unknown/partial usage checks passed.

- Build reusable pandas analytics over normalized increments; keep metric logic independent of Streamlit rendering.
- Support date, project, model, session and agent-role filters now, with a defined integration path for labels, task type and execution mode in Phase 2.
- Define timezone handling, daily/weekly/monthly buckets, filter intersection and empty/missing-value behavior.
- Provide tokens, input/output distribution, cache percentage, distinct sessions/agents, subagent share, and grouping by project/model/session. Add run and label aggregation in task 10.
- Specify how agent filters affect hierarchy context and totals, and how overlapping runs or multiple labels avoid duplicating global usage.
- Carry observed/manual/estimated provenance and completeness through aggregate results.

## Acceptance and validation

- Deterministic fixtures verify cross-filter intersections, bucket boundaries, distinct counts, weighted cache ratios, unknown values and empty results.
- Every consuming view uses this shared contract; no chart maintains a separate conflicting total calculation.

## Decisions and validation evidence

- All filters intersect. Dates are inclusive UTC calendar days; timestamps are converted to UTC, and absent or invalid timestamps are excluded only when a date filter is active. Daily buckets begin at UTC midnight, weekly buckets on Monday UTC and monthly buckets on the first UTC day; missing timestamps retain an unknown bucket. No selection means unrestricted; an empty selection matches nothing and missing dimensions do not match selected values.
- Metrics operate on accounting increments, carry source references and observed-counter/estimated-timing provenance, preserve unknown and partial totals, and use task 03's weighted paired cache ratio. Distinct counts cover observed sessions and agents, including those with no token record; selected sessions without counters make mixed totals partial. Main/subagent share remains unknown because parent inclusion is unresolved. A known ancestor and descendant are never combined even when an intermediate agent is filtered out. Group totals can overlap and must not be summed to infer a global total.
- Agent-role filters select usage rows only; hierarchy evidence remains available from the full event collection as context, not as additional usage. Phase 2 should join run and label metadata to increment identities via a membership filter, deduplicating references before global aggregation; overlapping runs or multiple labels must not multiply global usage. Task type and execution mode belong in that same filter layer, with manual provenance retained. Run/label aggregation remains deferred to task 10.
- Inline synthetic checks passed intersection of project, model, role and dates, UTC offset and week/month boundaries, distinct counts, weighted cache ratio, unknown groups, partial values and empty results. Python compilation passed; consuming views are implemented in task 06. Independent review pending.


- Review fix: inline checks confirmed metadata-only and mixed sessions count under intersected date/project/model/role filters and grouping, usage is not duplicated, metadata-only totals remain unknown, and mixed totals are partial. Compilation passed; independent re-review pending.

