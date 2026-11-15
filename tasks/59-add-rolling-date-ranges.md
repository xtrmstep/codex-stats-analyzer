## Title

Add 7-day and 30-day Overview date ranges

## Specification

Follow the [sidebar Date range presets](../specification/01-screens/010-navigation.md#date-range). This is a standalone UI task.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), extend `_date_limits(preset, today)` with **Last 7 days** and **Last 30 days**. Use `(today - timedelta(days=6), today)` and `(today - timedelta(days=29), today)` respectively. Both limits are inclusive.
- Add both presets to the existing sidebar selector and set **Last 7 days** as the initial selection for a fresh Overview. Retain the `overview_date_range` key and preserve the relative order of the existing presets. Reuse the same local `date.today()` per render, the existing date labels and bounds mapping, and the current `Filters(start_date=..., end_date=...)` path.
- Keep existing calendar presets, saved markers, sidebar filter eligibility, report calculations, and time aggregation. Limit application changes to `dashboard.py`.

## Acceptance Criteria

- A fresh Overview defaults to **Last 7 days**. Both new options show their inclusive dates in the menu and in the selected value. An explicitly selected preset remains selected across Overview rerenders.
- For a local date of January 1, 2027, the displayed and applied limits are December 26 through January 1 for **Last 7 days** and December 3 through January 1 for **Last 30 days**. Records with today's recorded date are included in both presets.
- **Today**, **All Time**, **Last week**, and **Last month** retain their existing bounds. Chat and Agent eligibility and both reporting windows use the selected bounds. A saved marker still adds its inclusive cutoff to the comparison window.
