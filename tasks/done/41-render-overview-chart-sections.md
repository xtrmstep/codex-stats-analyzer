## Title

Show the seven Overview charts together

## Dependencies

Task 40 supplies the grouped measurements. Use the existing date range controls available when this task starts.

## Specification

Follow the [Overview chart layout](../specification/01-screens/030-content.md#3222-trends-and-charts). Preserve the [reporting windows](../specification/01-screens/030-content.md#reporting-windows).

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), delete the **Usage view** selectbox and stop passing `view` into `render_statistics()`. Leave the date range, refresh, time aggregation, and sidebar filters in place.
- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), call `StatsCalculation.calculate()` once per report. Under each scope's KPIs render the four trends then the three whole-window charts in specification order. Reuse existing Plotly bar chart rendering with **Total tokens** as the value, and use projects, agents, or models as the series for trends. In **Agent by project over time**, use project panels within one figure with a consistent time axis and the agent as the series. Use stable, unique chart keys for each scope and breakdown.
- Reuse chronological bucket ordering and the existing date-axis approach. If a trend contains an unknown bucket, use an explicit ordered category axis with **Unknown** last. Keep coverage available on hover. Render chart-local empty feedback when there are no plottable totals, and preserve **No time in range** for empty scope intersections. Keep the KPI values and show cached and non-cached input totals as metrics alongside the existing KPI block.
- Replace the single-breakdown table with the chart sections. Keep **Download usage CSV**, the existing columns, and one scope summary row before that scope's breakdown rows. Use the seven chart measurement names, populate Project, Agent, Model, and Time from the appropriate grouping, and use the same ordered measurements as the charts. Remove the selector-specific renderer branches, table code, and the obsolete whole-window **Agent by project** registry entry and calculator in [`usage_statistics.py`](../src/internal/analytics/usage_statistics.py). Use the existing **Model** result for the **By model** chart and CSV label. Remove local imports, parameters, and return plumbing that become unused. Retain shared pandas, Plotly, and CSV helpers.

## Acceptance Criteria

- Overview shows four time charts followed by three summary charts per reporting window with plottable data, with the requested titles and no Usage view selector. A selected marker displays the same layout for both windows when both have data.
- Date and sidebar filters apply to every chart. Trends stay oldest to newest even when series begin in different buckets. The project panels keep the same agent separate across projects. Changing the time aggregation rebuckets the trends and leaves the summary totals unchanged.
- The CSV has one summary row per scope and covers each chart breakdown in its display order. Empty ranges and unknown totals remain distinguishable from zero, chart keys are unique with both scopes visible, and refresh, Manual annotations, and existing filter interactions still work.
