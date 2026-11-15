## Title

Use short project labels throughout Overview charts

## Specification

Follow the [Overview chart labels](../specification/01-screens/030-content.md#3222-trends-and-charts). Reuse the shared snapshot mapping from tasks 72 and 73.

## Work

- Pass the shared project label mapping from [`dashboard.py`](../src/internal/ui/dashboard.py) to `render_statistics()` in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py). In `_render_chart()`, use it when turning grouped measurements into Plotly rows. Apply display labels to the project axis, legend, facets, and hover text wherever applicable, including **Project over time**, **By project**, and **Agent by project**. Keep unattributed usage labeled **Unknown**.
- Use the same mapping in the selected-period charts and either comparison mode. Keep chronological time ordering and order project categories by display label. Keep project keys in the calculators and use the distinct labels only for presentation.

## Acceptance Criteria

- Charts show the same short labels as the Projects filter. The selected and comparison sides show the same label for a project, and neither side exposes full identifiers in chart text or hover details.
- Two projects with the same base label remain distinct chart categories or series. Counts, totals, filters, bucket order, and empty states stay unchanged.
