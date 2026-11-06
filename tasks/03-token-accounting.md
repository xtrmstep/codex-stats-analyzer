# 03 — Token increments and trustworthy totals

Status: Not started | Phase: 1 | Dependencies: 02

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
