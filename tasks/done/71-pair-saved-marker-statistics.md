## Title

Show saved marker statistics in the paired Overview layout

## Specification

Follow the [reporting windows](../specification/01-screens/030-content.md#reporting-windows). Use the mutually exclusive controls from task 70.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), reuse `_comparison_execution_ids()` for either comparison when Chat or Agent is selected. Match those selections by title and reporting name across the snapshot so a qualifying execution can contribute even if it falls outside the selected dates. Keep the selected-period execution IDs unchanged.
- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), request the selected window without a marker and use a second request for the active comparison on the same calculator. For a marker, use its offset-bearing timestamp as the inclusive instant `start`, clear `start_date`, and retain the selected `end_date`. Reuse the existing cutoff and **All Time** horizon in [`StatsCalculation.calculate()`](../src/internal/analytics/usage_statistics.py). Keep filters, time aggregation, and previous-period bounds on their existing paths.
- Feed both comparison modes into the same KPI column and chart pairs. For a marker, use **Since [marker name]** in the KPI header and chart heading and display the marker timestamp and comparison end. Render the name as text so punctuation in it leaves the table intact. Remove the separate marker render path. Keep the empty comparison on the right and preserve the standard layout when neither option is active.

## Acceptance Criteria

- With October 12–18 selected, a marker at October 10, 09:30 starts the comparison at that instant, including earlier qualifying rows through October 18. A marker within the range includes usage exactly at the cutoff. A marker after the end shows **Unknown** comparison KPIs and **No time in range** on the right while retaining the selected results.
- With **All Time**, a marker uses the report horizon. Both sides honor the same active filters and time aggregation, including matches by chat title and agent name that occur only in the marker window.
- Previous-period comparison still uses **Previous period** and its existing bounds. With neither option active, the report keeps the three-column KPI table and single-column charts. Manual Annotations and persisted marker data are unaffected.
