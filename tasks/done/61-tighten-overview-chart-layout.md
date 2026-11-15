## Title

Tighten the Overview chart layout

## Specification

Follow the [Overview chart layout](../specification/01-screens/030-content.md#3222-trends-and-charts). This task is independent of the KPI table styling.

## Work

- In the chart loop in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), use compact chart headings and set height and margins with `figure.update_layout()` before `st.plotly_chart()`. Start around 300 pixels for trends and 260 pixels for summary charts. Keep the existing single-column width and chart order. Allow more room for the project facets or for labels and legends that need it.
- Leave the seven chart definitions, date and category order, series, project facets, hover fields, chart keys, and empty-chart feedback intact. Apply the same presentation in both reporting windows. Keep sizing in the existing renderer, with no new settings or dependencies.

## Acceptance Criteria

- The seven charts use less vertical space at the same desktop width and still appear in order in both sections and both reporting windows. Titles, ticks, legends, and project facet labels remain readable with multiple series and longer labels.
- With the sidebar open and at a narrower width, the chart remains usable and its axis and hover data stay available. Verify chronological trends and a chart with no plottable data. Token values, filters, time aggregation, and KPI content are unchanged.

## Issue Logs

### Failed check 1
- In the agent-by-project trend from `src/internal/ui/statistics_ui.py`, the first compact rendering showed overlapping date ticks across adjacent project facets when several projects were displayed.
- This violates the requirement that ticks remain readable with multiple project panels.
- Reduce facet tick density and format dates compactly while preserving the underlying time axis and aggregation.

### Failed check 2
- After shortening and reducing ticks, adjacent facet date labels still touch at the panel boundaries in the rendered project trend in `src/internal/ui/statistics_ui.py`.
- This continues to violate the multi-project tick readability criterion.
- Increase horizontal spacing between facets and further reduce tick density, then inspect the rendered result.
