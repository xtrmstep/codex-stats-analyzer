## Title

Show paired previous-period charts and enable comparison

## Specification

Follow the [sidebar checkbox](../specification/01-screens/010-navigation.md#compare-to-previous-period) and [chart layout](../specification/01-screens/030-content.md#3222-trends-and-charts). Requires the results from task 63 and the KPI column from task 64.

## Work

- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), reuse the current chart rendering logic and chart definitions for both periods. Add **Selected period** and **Previous period** headings with each period's inclusive dates. Render one two-cell row per chart definition and use distinct Streamlit keys for each period. Keep the existing section order, groupings, chronological trends, and chart empty states.
- In [`dashboard.py`](../src/internal/ui/dashboard.py), add **Compare to previous period** below **Time aggregation**, unchecked by default. Disable it for **All Time** and supply comparison bounds and execution IDs only for an enabled comparison with a bounded range. Keep the marker report separate and render its charts in a single column.

## Acceptance Criteria

- Enabling comparison for a bounded preset displays the additional KPI values and paired charts. The left and right headings show the selected and previous dates, and each pair stays aligned even if one period has no plottable usage.
- Date range, filters, and time aggregation update both periods. Turning comparison off or selecting **All Time** restores the three-column KPI table and single-column chart layout. A selected marker still displays its own report below the Overview.
