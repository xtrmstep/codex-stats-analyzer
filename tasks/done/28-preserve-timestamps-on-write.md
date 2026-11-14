## Title

Preserve source and local timestamps on write

## Goal

Store valid Codex timestamps as recorded and generate application-owned timestamps in machine-local time with an offset. This task is limited to writes and ingestion comparisons.

## Work

- In `src/internal/ingestion/transformations.py`, replace `_utc()` with validation that retains the original valid timestamp text, including the offset or `Z` and all source fractional digits. Apply it to usage observations, previous observations, and coverage diagnostics. Keep existing handling of invalid or missing timestamps.
- In the same module, review response deduplication and legacy counter ordering. Compare valid timestamps as instants using their offsets. Two spellings of the same instant must not create a conflicting response. Use the chosen source record's timestamp for storage. Leave token counts, identity and attribution rules, and overlap handling in place.
- In `src/internal/analytics/usage_statistics.py`, keep `save_marker()` validation and chat scope but store the timestamp text entered by the user. In `src/internal/ui/statistics_ui.py`, use machine-local time with an explicit offset for the new-marker default. Keep marker editing, deletion, and validation behavior.
- In `src/internal/ingestion/collection.py` and `src/internal/metadata/experiment_store.py`, generate new collection and experiment-history timestamps in machine-local time with an explicit offset. Leave the existing collection, publication, and history operations in place.
- Update the timestamp storage rule in the [usage data model](../specification/02-architecture/02-design/010-usage-data-model.md). Keep the current dashboard display behavior for this task. The [saved marker behavior](../specification/01-screens/030-content.md#saved-time-markers) still applies.

## Acceptance Criteria

- A fresh import stores `2026-11-14T23:30:00.123456789-05:00` exactly as recorded. Source `Z` and `+00:00` values also survive unchanged. SQLite-only replay reproduces the stored usage timestamps.
- Equivalent instants with different offsets still deduplicate, and legacy ordering and diagnostics still use the correct event sequence.
- A newly saved marker retains its entered timestamp and selected-chat scope after reopening. Generated timestamps carry the machine's local offset. Raw JSONL bytes and report publication behavior remain intact.
- Verify with a fresh database. Schema upgrades, backfills, and compatibility changes for existing data are outside the task.
