## Title

Remove the unused cumulative accounting code and its private callers

## Dependencies

Tasks 50 and 51 remove the current application's cumulative counter consumers.

## Specification

The supported application consists of [Overview and Manual annotations](../specification/01-screens/010-navigation.md#12-supported-sections).

## Work

- In [`token_accounting.py`](../src/internal/analytics/token_accounting.py), remove `calculate_increments()`, `Increment`, `AccountingResult`, cumulative-only aggregation, and helpers once the remaining callers are gone. Keep `calculate_response_usage()`, its token fields, and the shared timestamp parser. In [`parser.py`](../src/internal/ingestion/parser.py), remove the unused direct file ingestion entry point if a reference check confirms it has no callers. Keep file discovery, source byte reads, and `parse_collected()`.
- Audit the remaining private callers in `src/internal/analytics/agents.py`, `src/internal/analytics/metrics.py`, and the disconnected run, label, and experiment modules under `src/internal/metadata/` and `src/internal/ui/`. Remove the unreachable cumulative reporting code and modules that exist solely for those retired views. Retain the observed-event filter helpers and fields used by Overview, and retain current agent names, saved markers, and exports. Update stale documentation that describes retired reporting features as available. Leave existing user-authored JSON files on disk.

## Acceptance Criteria

- Source search finds no cumulative counter calculation, cumulative reporting branches, or imports of removed symbols in the application. Current entry points import successfully, and shared timestamp parsing and response validation still run.
- Overview filters and reporting, refresh actions, and Manual annotations operate through their current entry points. Current SQLite data and historical user-authored files are preserved.

## Issue Logs

### Failed check 1
- `git diff --check` reports an extra blank line at the end of `src/internal/analytics/metrics.py` after removing retired code.
- This fails the repository's required clean static checks for the task.
- Remove the extra trailing blank line and rerun the checks.
