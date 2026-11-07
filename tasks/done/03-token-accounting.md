# 03 — Token increments and trustworthy totals

Status: Complete; independent review passed | Phase: 1 | Dependencies: 02

Specification: §3.3; MVP 2, 13.

## Scope

- Determine counter scope and derive consumption from increments. Document first-counter, reset, repeated-counter, out-of-order, and model-change handling using observed formats.
- Preserve total, input, cached input, non-cached input, output and reasoning output counts, including unknown values and completeness metadata.
- Define total and component relationships explicitly; do not add reasoning output or cached input again when already included in their parent counters.
- Compute cache percentage from eligible summed cached input divided by eligible summed input, with unknown or zero denominators handled explicitly.
- Associate increments with source events, timestamps, sessions, agents and models. Preserve timing uncertainty for later interval attribution.
- Detect whether parent counters include child usage and establish a single accounting path for each usage record. Unresolved attribution must remain visible.

## Acceptance and validation

- Hand-calculated fixtures verify counter deltas, resets, duplicates, missing fields, changing models, and nested-agent rollups.
- Unknown values remain unknown rather than becoming zero; negative or inconsistent counters produce diagnostics.
- Session totals and disjoint agent/model totals reconcile where source coverage permits. Partial totals are marked as partial.

## Decisions and validation evidence

- Independent Astra re-review passed at `09e91a3`, with both original edge cases reproduced successfully after fixes. No blocking findings remain; parent rollup uncertainty is a documented limitation.

- Sampled only key shapes in local files: both event-message total and thread-usage cumulative records contain input, cached input, output, reasoning output and total counters. Prefer event-message totals per session where present, otherwise thread totals; their overlap is unverified, so never add the two families. Per-response and last-usage counters are not added independently.
- The first observed cumulative snapshot is a partial baseline from zero. Repeated counters produce zero increments, duplicate references are ignored, timestamp regressions are excluded, and counter decreases start a partial reset epoch. Missing, invalid and inconsistent values stay unknown or partial. Input includes cached input; output includes reasoning output; neither child is added to its parent. Non-cached input is the difference. Cache percentage uses paired eligible summed counters and is unknown for zero input.
- A counter is timestamped at observation, not exact usage time. Model context carries forward, but first snapshots and deltas crossing a model change have unknown model attribution. Session ID is the fallback agent identity. Parent and child streams are not summed when their relationship is known because counter inclusion is unresolved; the combined aggregate is unknown. Full scope and hierarchy reconciliation require later evidence; partial totals do not imply complete coverage.
- Inline hand-calculated synthetic checks passed for deltas, duplicates, reset, invalid fields, timestamp regression, model change, eligible cache ratio, and unresolved parent-child aggregation. Python compilation passed. Independent review pending.

- Review fixes: inline checks confirmed inconsistent derived reasoning and total increments are diagnosed and remain unknown. A separate A → B → A model sequence now leaves the crossing increment unattributed while the next stable interval is attributed. Compilation passed; independent re-review remains pending.
