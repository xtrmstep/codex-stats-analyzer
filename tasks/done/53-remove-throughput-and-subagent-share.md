## Title

Remove Turn throughput and Subagent share from Overview

## Specification

Follow the [Overview KPI list](../specification/01-screens/030-content.md#3221-overview-kpis) and the [token accounting rules](../specification/02-architecture/02-design/020-backend-class-design.md#token-accounting). This is a standalone implementation task.

## Work

- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), remove the **Turn throughput** and **Subagent share** cards and their tooltips from the reporting-window summary. Use a two-column second row for **Cached input** and **Non-cached input**. Remove `Subagent share %` from `_row()` and the CSV column mapping. The emitted header is `subagent_share_percentage`. Keep the rest of the CSV fields and their order.
- In [`usage_statistics.py`](../src/internal/analytics/usage_statistics.py), remove `turn_throughput` and `subagent_share` from `UsageMeasurement`. Remove the share calculation from `_measure()` and update its construction of `UsageMeasurement`. Drop the parent-ID projection from the report's usage query, while keeping it on stored agent threads. Delete `_index_turn_events()`, `_turn_duration_in_window()`, `_turn_output_tokens()`, `_turn_throughput()`, and the throughput call in `StatsCalculation.calculate()`. Remove the unused `json` import and keep `dataclasses.replace` for the observed agent count. Preserve the shared coverage checks and date and marker comparisons.
- In [`parser.py`](../src/internal/ingestion/parser.py), remove the evidence block for `task_started`, `task_complete`, and `turn_aborted` that is used solely for throughput. Remove the unused `math` import. Keep normal event parsing, recorded timestamps, turn identifiers, agent evidence, and raw source lines. The metrics are calculated in memory, so the SQLite schema, importer, and source refresh paths need no changes.

## Acceptance Criteria

- Both reporting windows show the seven specified KPIs with their existing values and help text. The agent count, coverage indicator, and charts still render. Empty-window behavior is unchanged.
- The usage CSV omits only `subagent_share_percentage`. The existing report data remains available, and coverage and token values match the same input under the previous calculation.
- Application code has no remaining references to the two removed metrics or their dedicated timing extraction. Agent hierarchy, sidebar filters, saved markers, Manual annotations, and both refresh modes continue to work with the existing database.
