## Title

Remove cumulative counter processing from Overview filters

## Specification

Follow [Overview filtering and reporting windows](../specification/01-screens/030-content.md#reporting-windows). This task can be completed before removing the cumulative import path.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), remove the call to `calculate_increments(parsed.events)` and its import. Build the filter dataset from observed events only. The current `build_dataset(parsed.events, [])` can be used for this step to retain contextual project, model, role, dates, and execution identities. The report itself continues to read committed usage from `StatsCalculation`.
- Replace the dashboard's transient cumulative accounting diagnostics with the usage diagnostics already loaded from the committed publication. Keep the existing parsing diagnostics. Preserve the resolved project filtering, Chat and Agent name matching and resets, and the observed-events empty state. Keep both report windows and the CSV.

## Acceptance Criteria

- Rendering Overview or changing filters runs no cumulative counter calculation. An observed execution can still participate in the filter options even when it has no supported response usage.
- Date, project, model, role, Chat, and Agent selections work with the same recorded metadata. Parsing and committed usage diagnostics remain visible. Charts and KPI token amounts still come from `StatsCalculation`.
