## Title

Import and report per-response token usage only

## Specification

Follow the [response-only accounting rules](../specification/02-architecture/02-design/020-backend-class-design.md#token-accounting) and [`CodexUsage` model](../specification/02-architecture/02-design/010-usage-data-model.md#codexusage). Keep collection of original source lines, execution metadata, and user annotations.

## Work

- In [`parser.py`](../src/internal/ingestion/parser.py), keep response-level `usage`, its identifiers and timing, and existing event metadata. Remove extraction of cumulative `event_msg.token_count` counters and the turn/thread rollup counters from `token_usage_record`. Preserve original source bytes and observed events that supply filter, hierarchy, or timing context.
- In [`transformations.py`](../src/internal/ingestion/transformations.py), remove the `legacy_events` path, cumulative delta calculation, overlap diagnostics, and coverage propagation driven by those diagnostics. Keep response counter validation, deduplication, owner and context checks, and genuine response diagnostics. Remove `prior_observed_at` and `counter_provenance` from `CodexUsage` and its destination mapping.
- In [`usage_statistics.py`](../src/internal/analytics/usage_statistics.py), remove legacy interval and overlap handling in `calculate()` and `UsageCalculator.groups()`, and redundant provenance checks in throughput and subagent share. Keep the per-response coverage checks, actual response conflicts, hierarchy safeguards, recorded-date filters, chronological buckets, and marker cutoff. Update the coverage caption in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py) to describe response coverage.
- In [`collection.py`](../src/internal/ingestion/collection.py), use the existing schema-version and `needs_rebuild` mechanism to replace the derived `usage_records` structure and invalidate the pre-change publication. Rebuild from SQLite on first use so stale delta rows, legacy diagnostics, and propagated partial flags leave the report without requiring a source scan. Update the schema atomically and keep raw lines, chat-title evidence, incremental checkpoints, saved markers, and assigned agent names. Keep both refresh modes working and preserve the existing failure diagnostics for an unsuccessful rebuild.
- Update the source format description in [`README.md`](../README.md) to reflect response-only totals. Keep `calculate_response_usage()` and shared timestamp parsing for their current callers.

## Acceptance Criteria

- A response plus associated cumulative or rollup counters counts once. A cumulative-only log still preserves source records and observed metadata, with no calculated token amount. Confirm genuine response duplicates and conflicts retain their existing handling.
- Rebuilding an existing SQLite archive removes stale cumulative rows and their coverage diagnostics without changing original records or user metadata. An empty database and both refresh modes produce the same response-only schema and reports.
- A completed, fully verified turn with matching responses can produce numeric throughput even when its logs also contain cumulative counters or appear in multiple files. Missing or conflicting response evidence, or a turn clipped by the selected filters or window, retains existing rejection behavior. Verify token amounts and scope limits in both report windows. Where the affected SQLite archive is available, verify on a disposable copy that any remaining **Unknown** result has a response or timing cause.
