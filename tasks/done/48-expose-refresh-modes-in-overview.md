## Title

Expose both refresh modes in Overview

## Dependencies

Task 46 optimizes `refresh()`. Task 47 provides `full_refresh()`.

## Specification

Follow the [Overview refresh controls](../specification/01-screens/030-content.md#321-view-parameters--view-configuration).

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), replace the current **Refresh sources** action with **Incremental refresh** and **Full refresh from source** in the Overview configuration. Place concise help beside the full refresh control explaining that it replaces imported history with available source logs and keeps saved markers and agent names.
- Route the two actions to `importer.refresh(sources)` and `importer.full_refresh(sources)` respectively. Run one import action per request. Keep first-use loading and the existing SQLite rebuild path when `needs_rebuild` is set. Reuse diagnostic and last-published-report handling for both actions. Update the no-publication retry message to name **Incremental refresh**.
- In [`README.md`](../README.md), describe which action to use for new data and which replaces imported data. Keep date range, filters, time aggregation, Manual annotations, and the report layout as they are. Both refresh actions use all configured source folders, while report filters limit the displayed results.

## Acceptance Criteria

- Each Overview action calls only its matching importer operation. A regular page or filter rerun after initialization does not trigger a refresh. Startup behavior and Manual annotations are unchanged.
- Both actions show diagnostics on failure and display the last committed report when available. A successful refresh updates the report using the active date range and filters. Full refresh help is visible before the action is triggered.
