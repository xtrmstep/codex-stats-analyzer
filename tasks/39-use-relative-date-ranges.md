## Title

Offer relative date ranges in Overview

## Specification

Follow the [Overview date range](../specification/01-screens/030-content.md#date-range). This task has no pending prerequisites.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), put a single **Date range** selectbox in `_render()` inside **Overview configuration**, after the Manual annotations early return. Offer the six specified presets with **Today** selected by default. Remove the `render()` date controls, the `range_ready` variable and argument, the incomplete-range message and early return, and the conditional branch around `filter_dataset()`. Since `_render()` resolves the dates, remove `start` and `end` from its call and signature as well.
- Resolve the preset once per Overview render from `date.today()`. Pass the same pair of `date` values into the existing `Filters(start_date=..., end_date=...)`, with `(None, None)` for **All Time**. Use `today.weekday()` to find Monday, and `today.replace(day=1)` to find the first of the current month. For **Last week**, subtract seven days and one day from this Monday to get the inclusive endpoints. For **Last month**, take the day before this month's first day and use its first day as the start. Use standard-library date arithmetic and keep preset resolution in the dashboard.
- Keep `filter_dataset()` and the existing `render_statistics()` request path. The resolved dates constrain the Chat and Agent options and the same report windows used by the charts, table, and CSV. Keep recorded-date matching, stored timestamps and offsets, marker cutoffs, time aggregation, other filters, and Manual annotations behavior. Work is limited to the Overview UI and preset resolution. No schema or stored data changes are needed.

## Acceptance Criteria

- A fresh Overview shows **Today**. The selector offers exactly the six specified presets. Manual annotations has no date-range selector.
- **Today** matches the app's local date against each event's recorded calendar date. **Current week** and **Current month** include today. **Last week** is a full Monday-to-Sunday week, **Last month** is a full calendar month, and **All Time** adds no date limits. Verify boundaries on Monday, across December and January, and when the previous month is February in a leap year.
- A preset change updates Chat and Agent eligibility and both reporting windows using the same inclusive dates. Verify a marker inside the range and one after the range, along with the unchanged CSV columns and time aggregation controls.
