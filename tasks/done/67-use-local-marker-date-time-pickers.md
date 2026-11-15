## Title

Use local date and time pickers for markers

## Specification

Follow the [Manual Annotations editor](../specification/01-screens/030-content.md#34-manual-annotations). This updates the marker form independently of the listing and navigation changes in task 66.

## Work

- In `marker_editor()` in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), replace the timestamp text field with Streamlit **Date** and **Time** pickers. Use the app host's local time zone, matching the table, and indicate the zone beside the controls. Initialize a new marker to the current local date and time. Prefill an existing marker from its stored instant converted to local time. Keep form values tied to the selected marker so switching records loads the right defaults.
- Combine the inputs on save and resolve the offset for that local date and time. Show a validation message for skipped or repeated times introduced by an edit or new entry. Reuse `save_marker()` and the existing offset-bearing timestamp format. When the displayed date and time have not changed, pass the original timestamp through to preserve its precision and instant.

## Acceptance Criteria

- New markers start at the current local date and time. Switching between saved markers shows each marker's local values. Saving a name-only edit preserves the original timestamp and the Overview cutoff.
- A changed date receives the correct local offset, including on either side of a daylight-saving transition. A skipped or repeated time shows a validation message and leaves the saved entry intact. The Overview uses the new cutoff after a valid save.
