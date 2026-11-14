## Title

Use recorded timestamps in reports and remove the display time zone control

## Goal

Use the calendar date and clock time as recorded for report filtering and grouping. Preserve timestamps and offsets in displayed observations and exports. This task can be verified with seeded offset-bearing SQLite records independently of ingestion changes.

## Work

- In `src/internal/ui/statistics_ui.py`, remove `display_timezone()`, its IANA validation, and its widget and session state keys. Remove the `zone` argument from `render_statistics()` and format marker and range labels from the supplied values. In `src/internal/ui/dashboard.py`, remove the selector call and zone wiring. Keep the shared header's **All Time** default and custom range interaction, and leave the two-page shell and Overview control placement in place. See the [header specification](../specification/01-screens/020-header.md#22-header-elements).
- In `src/internal/analytics/metrics.py`, remove `Filters.time_zone` and replace UTC-only frame parsing and date and bucket logic. Keep each valid timestamp's recorded clock components. Use inclusive written calendar dates for custom range selection. Apply the same rule in `src/internal/analytics/usage_statistics.py`. Remove `StatsRequest.time_zone`, UTC coercion, and configured-zone bucketing. Keep hourly, daily, Monday-start weekly, and monthly grouping. For chart buckets use calendar and clock labels consistently when a report mixes offsets.
- In `StatsCalculation` and `UsageCalculator`, use the recorded offsets for instant comparisons, exact marker cutoffs, and elapsed durations where verifiable. Keep date filtering separate from instant comparison. Apply both to usage, session and agent counts, and applicable coverage diagnostics. In `StatsCalculation.__init__`, generate the report time in machine-local time with an offset. Preserve the [reporting windows](../specification/01-screens/030-content.md#reporting-windows), including the all-chat or selected-chat scope, inclusive cutoff, empty-window message, and uncertain timing for legacy deltas crossing a cutoff. Keep averages unknown when elapsed duration cannot be established.
- In `dashboard.py`, replace forced UTC parsing for session first and last observations and timeline endpoints. Use offset-aware ordering and overlap checks where the source establishes the instants. Keep original timestamp representations available in displayed values and timeline details. In `src/internal/ui/exports.py`, update the session timestamp labels and CSV keys to omit the UTC suffix. Keep CSV encoding, units, unknown-value handling, and other fields in place.
- Remove `time_zone` and the dashboard time zone rule from the [data model](../specification/02-architecture/02-design/010-usage-data-model.md). Update the [content specification](../specification/01-screens/030-content.md) and `README.md` to describe recorded-date filters, buckets, and timestamp display.

## Acceptance Criteria

- **Display time zone** is absent. **All Time**, custom ranges, existing dimension and sort controls, marker management and scope, session detail, session comparisons, timelines, and exports are usable.
- A record at `23:30-05:00` appears on the written date in filters, in the `23:00` hourly bucket, and with its recorded offset in observation labels and exports. Verify all four bucket sizes, mixed offsets, and a source timestamp already written in UTC. Charts, tables, and exports agree on the included records.
- Exact marker comparisons treat equivalent instants equally. The full selected period and the marker window retain their existing scopes, and a legacy delta crossing the marker still reports uncertain attribution.
- Filters and marker changes use the committed dataset. A failed refresh still shows the last successful publication. This task makes no changes to ingestion, counter accounting, SQLite schema, or historical data.
