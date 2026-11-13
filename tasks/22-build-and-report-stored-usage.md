## Title

Build usage reports from collected Codex records

## Goal

Rebuild usage from the retained logs and compare the selected reporting period with the period since a saved time marker.

## Dependencies

- [Task 21](./21-collect-original-codex-records.md) provides the persisted records and raw store operations.

## Work

- Implement `UsageBuilder` and extend `UsageStore` to publish and query `AgentThread` and `Usage` according to the [backend design](../specification/02-architecture/02-design/000-system-overview.md#usage-rebuild-and-accounting). Reuse existing parsing and accounting where it supports the specified thread identity, usage attribution, and coverage rules.
- Wire source refresh to collect records and then rebuild usage. Read the last committed dataset for dashboard filtering and export.
- Persist `TimeMarker` and implement the [saved time marker behavior](../specification/codex-usage-analyzer.md#54-saved-time-markers) and [reporting windows](../specification/codex-usage-analyzer.md#63-visualizations).

## Acceptance Criteria

- Rebuilding after removing access to the original logs yields the same results from the same collected records. Duplicate or overlapping evidence is accounted for according to the specification.
- A failed collection or rebuild leaves the last usable metrics available and reports the failure. A successful rebuild preserves collected records, saved markers, and existing annotations.
- Project-by-time, agent-by-time, and agent-by-project views query the stored dataset with consistent attribution and coverage in reports and exports.
- Selecting a saved marker shows both metric windows with the same filters and independent daily averages. Empty intersections and legacy intervals crossing a cutoff follow the product specification.
