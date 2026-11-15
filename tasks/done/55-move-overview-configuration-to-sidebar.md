## Title

Move Overview configuration to the sidebar

## Specification

Follow the [sidebar configuration](../specification/01-screens/010-navigation.md#16-overview-configuration) and the [main content refresh layout](../specification/01-screens/030-content.md#321-refresh-actions).

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), move the **Overview configuration** heading, **Date range** selectbox, and **Time aggregation** radio into the sidebar after **Navigation** and before the **Filters** container. Keep the widgets in the Overview branch of `_render()`. Reuse the date preset labels, `_date_limits()`, date selectbox key, and aggregation values and default. Keep passing the same bounds and bucket to the report.
- Keep both refresh buttons side by side at the top of the main content, using the existing refresh flags and full-refresh help. Preserve import routing, diagnostic handling, and Manual annotations.

## Acceptance Criteria

- On Overview, the sidebar order is **Navigation**, **Overview configuration**, **Filters**. Both refresh actions remain at the top of the main content on a single row.
- Select **Last week** and confirm the selector displays its bounds and the report uses them. Switch aggregation from daily to weekly and confirm that trends rebucket with the same summary totals. Both refresh actions and the Manual annotations layout continue to work.
