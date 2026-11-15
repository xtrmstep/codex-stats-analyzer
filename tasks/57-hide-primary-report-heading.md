## Title

Remove the Full selected period heading

## Specification

Follow the [reporting windows](../specification/01-screens/030-content.md#reporting-windows).

## Work

- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), render the scope subheading only for the marker window. Keep the existing marker timestamp caption in that window. Start the primary window with its date and coverage caption where applicable, followed by its KPIs and charts.
- Keep the internal **Full selected period** scope key in `StatsCalculation`. Keep output order, filters, effective bounds, calculations, and scope-specific chart keys.

## Acceptance Criteria

- With no marker selected, the main report still displays its date and coverage, seven KPIs, and charts. There is no **Full selected period** heading.
- With a marker inside the date range, the primary report is followed by **Since [marker name]** with its timestamp and comparison report. With a marker after the date range, the second window retains its heading and **No time in range** message. Primary totals remain unchanged for the same filters.
