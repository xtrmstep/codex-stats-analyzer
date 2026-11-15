## Title

Calculate and display turn throughput for each reporting window

## Dependencies

Task 44 exposes lifecycle timing. Task 43 establishes the KPI label and help in the report summary.

## Specification

Follow the [turn throughput rule](../specification/02-architecture/02-design/020-backend-class-design.md#token-accounting) and the [reporting windows](../specification/01-screens/030-content.md#reporting-windows).

## Work

- In [`usage_statistics.py`](../src/internal/analytics/usage_statistics.py), use the already replayed events and usage rows from the same committed snapshot. Match lifecycle and response usage by verified execution and `turn_id`. Use `source_record_id` to map committed usage rows to their parsed events, and the existing per-response identities to recognize duplicate observations. Count each response and turn duration once. Reject conflicting timing, missing or non-positive duration, failed or aborted turns, and turns whose output cannot be established from complete, independently counted response rows. Validate the complete response set against the parsed usage evidence so a withheld response cannot silently make a turn qualify. Leave legacy cumulative totals in their existing usage metrics.
- Evaluate eligible turns separately inside each `StatsCalculation.calculate()` reporting window. Both lifecycle endpoints must satisfy its recorded-date bounds, inclusive start and marker cutoff, and any explicit exclusive end. Reuse the existing recorded-date and instant comparison rules. Require all attributable response rows for an eligible turn to survive the scope and report filters, including a model or project filter that would otherwise select only part of a turn. Leave the existing usage-row selection and effective bounds unchanged.
- Add a nullable in-memory throughput value to the scope `UsageMeasurement`. Compute `sum(output_tokens) * 1000 / sum(duration_ms)` over eligible turns. Count concurrent turns by summing their individual durations and keep the value independent of chart buckets. In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), use the value in the existing **Turn throughput** KPI, formatted in `tokens/s` with `_number()` and displayed as **Unknown** when absent. Preserve the help, other KPIs, charts, and CSV columns. No additional data read or schema change is needed.

## Acceptance Criteria

- Complete eligible turns with 900 output tokens in 20 seconds and 300 in 10 seconds produce **40.0 tokens/s**. Duplicate records have no effect. A qualifying zero-output sample renders zero. No eligible turns renders **Unknown**.
- A turn cut by a date boundary, saved marker, or partial model or project filter is excluded from throughput for that scope while its eligible usage still contributes to the existing token metrics. Verify that both windows calculate separately, including a turn starting exactly at the marker.
- Aborted, failed, conflicting, and legacy-only turns leave throughput unknown if there are no other eligible turns. Time aggregation has no effect on throughput. Existing KPIs, their help, and CSV values remain intact.

## Issue Logs

### Failed check 1
- In `_turn_throughput` in `src/internal/analytics/usage_statistics.py`, repeated references to the same response record produced multiple candidate rows and rejected a valid turn.
- This violates the criterion that duplicate observations have no effect on throughput.
- Deduplicate candidate rows by their stable usage identity before validating the complete response set.
