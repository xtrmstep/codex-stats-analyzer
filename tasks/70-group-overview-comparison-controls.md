## Title

Group the Overview comparison controls

## Specification

Follow the [Overview comparison controls](../specification/01-screens/010-navigation.md#comparisons). The paired marker results are covered by task 71.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), move **Saved time marker** from **Filters** to **Overview configuration**, directly below **Compare to previous period**. Treat the checkbox as active only for a bounded date range.
- In `marker_selector()` in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), accept a disabled state. Give the selector a stable widget key so toggling the checkbox can preserve its selection. Keep **None** as the default and fall back to **None** if the selected marker no longer exists.
- Suppress the marker passed to `render_statistics()` while previous-period comparison is active. Keep the existing previous-period calculation and leave the other filter controls in place.

## Acceptance Criteria

- The controls appear together above **Filters**. By default the checkbox is unchecked and the marker selector is available with **None** selected.
- Selecting a marker and then enabling previous-period comparison disables the selector and applies only the previous period. Turning the checkbox off restores the still-valid marker. With **All Time**, the checkbox is disabled and the marker selector works even if it was disabled on the prior preset.
