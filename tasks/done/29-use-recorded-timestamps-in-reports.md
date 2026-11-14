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

## Issue Logs

### Failed check 1
- `src/internal/analytics/usage_statistics.py`: custom recorded-date ranges clear the effective end instant, so a marker after the selected period cannot trigger the required empty-window message.
- The reporting-window acceptance criterion requires an empty intersection to remain visible.
- Resolve marker-window emptiness using the selected dates and recorded offsets, without treating the date filter as a single global time zone; recheck mixed-offset boundaries and the displayed bounds.

### Failed check 2
- `src/internal/analytics/usage_statistics.py`: pandas timestamps truncate fractional digits beyond nanoseconds when comparing markers with observations; recorded values can contain more digits. Bucket rates are also always unknown even when all rows have the same offset and an elapsed interval is verifiable.
- This violates exact marker comparisons and the requirement to leave rates unknown only where elapsed duration cannot be established.
- Compare marker cutoffs with full-precision instant keys and calculate bucket durations when one recorded offset establishes the interval; retain unknown rates for mixed offsets.

### Failed check 3
- `src/internal/analytics/usage_statistics.py`: when a marker precedes a single-offset custom range, the marker window displays and uses the earlier marker as its effective start, which overstates elapsed duration.
- The marker window must represent the intersection with the selected period and use verifiable bounds for rates.
- Clamp the displayed/rate start to the selected range start when that bound is known, while retaining the exact marker instant for inclusion comparisons.

### Failed check 4
- `src/internal/ui/dashboard.py` formats parsed timestamps with `isoformat()`, which changes a source `Z` to `+00:00` and can truncate source precision in session and timeline details.
- The task requires original timestamp representations to remain available in displayed observations and exports.
- Retain timestamp text alongside parsed timestamps and use the original text for first/last observations and timeline endpoints while ordering by offset-aware instants.
