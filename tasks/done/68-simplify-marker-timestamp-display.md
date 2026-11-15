## Title

Simplify the marker timestamp column

## Specification

Follow the [Manual Annotations table](../specification/01-screens/030-content.md#34-manual-annotations). The row buttons and editor behavior are covered by task 69.

## Work

- In `marker_editor()` in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), rename the table column **Local date and time** to **Timestamp**. Keep the existing conversion to the app's local zone and display `YYYY-MM-DD HH:MM:SS` without a zone name or offset.
- Keep chronological ordering by the saved instant and preserve the offset-bearing timestamp in storage.

## Acceptance Criteria

- A saved marker with an offset different from the app's local zone displays the correct local date and time under **Timestamp**. The cell shows only the date and time.
- The table remains ordered from oldest to newest. The saved timestamp and the Overview cutoff remain unchanged.
