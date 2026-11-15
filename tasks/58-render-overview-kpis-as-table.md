## Title

Display Overview KPIs in a compact table

## Specification

Follow the [Overview KPI table](../specification/01-screens/030-content.md#3221-overview-kpis). This task changes the presentation of the existing measurements.

## Work

- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), replace both `st.columns()` KPI card blocks in `render_statistics()` with a single read-only table per reporting window. Show exactly **Name**, **Value**, and **Description**, with no row index or sorting controls. Keep the table above that window's charts and use the exact row order and formula descriptions from the specification.
- Populate **Value** from `summary.totals`, `summary.cache_percentage`, and `summary.average_daily_tokens`, using the same fields as the cards. Reuse `_number()` to preserve existing numeric formatting, the percentage suffix, and **Unknown**. The formulas are display text. Keep agent count and date and coverage captions, marker behavior, and charts in their existing places. Limit application changes to `statistics_ui.py`.

## Acceptance Criteria

- The table shows all seven KPI rows under the three required headers. **Total tokens**, **Input tokens**, and **Output tokens** are the first three rows. Formula descriptions are visible in the table.
- For the same date and filters the primary and **Since [marker]** tables show the same values as the previous cards. Check a zero and an unavailable value and confirm that they remain distinct. The percentage value still has a `%` suffix.
- A marker after the selected range retains **No time in range** for its empty window. The captions, chart values and order, and filter behavior are unchanged.
