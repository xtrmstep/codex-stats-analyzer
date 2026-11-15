## Title

Remove the Overview usage CSV download

## Dependencies

Complete task 53 first. It removes the subagent-share field while the CSV export is still available.

## Work

- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), remove the **Download usage CSV** button, its column mapping, the `export_rows` accumulator, and the summary and breakdown rows added only for that accumulator. Remove the `csv_bytes` import.
- Keep the row conversion used by Plotly. Limit it to `Project`, `Agent`, `Model`, `Time`, `Total tokens`, and `Coverage`, and remove the summary-only path. Preserve the existing measurement order, date axes, unknown categories, project panels, coverage hover, and empty-chart handling described in the [Overview specification](../specification/01-screens/030-content.md#3222-trends-and-charts).
- Delete [`exports.py`](../src/internal/ui/exports.py) after confirming it has no callers. Remove the CSV download paragraph from [`README.md`](../README.md) and rename **Filters and exports** to **Filters**. Leave the report calculations, sidebar options, refresh actions, and SQLite unchanged.

## Acceptance Criteria

- Overview has no usage CSV download in either reporting window. A source search finds no remaining CSV serializer, filename, or export action for the usage report.
- Both reporting windows retain the seven KPIs from task 53, the seven chart views, coverage details, date range and filters, and their existing empty states. Chart values, group names, and chronological order match the same report before export removal.
