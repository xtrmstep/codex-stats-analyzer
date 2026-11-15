## Title

Add marker row actions and open the editor on demand

## Specification

Follow the [Manual Annotations page](../specification/01-screens/030-content.md#34-manual-annotations). Keep the timestamp display from task 68.

## Work

- In `marker_editor()` in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), use aligned Streamlit columns for **Name**, **Timestamp**, and **Actions**, with native **Edit** and **Delete** buttons in each row's action cell. Key buttons by marker ID. Keep the existing ordering and empty-list message. Place **Add new** above the table and keep it available for an empty list.
- Replace the marker dropdown and always-visible form with session state for a closed form, a new marker, or the marker ID being edited. Render one shared form below the table. Initialize a new marker to a blank name and the local date and time when **Add new** is clicked. Prefill edits from the selected marker and key the inputs so changing rows loads the correct values.
- Use **Save** and reuse `save_marker()`, the local date and time pickers, and the existing time validation. Clear the editor state before rerunning after a successful save. Keep the form and its values visible on validation failure. Use `delete_marker()` for the clicked row, close the form if it was editing that marker, and rerun after deletion. Keep the Overview marker selector and persistence functions unchanged.

## Acceptance Criteria

- On entry the page shows **Add new** and the marker list without a form. **Add new** works from an empty list. Saving a new marker shows it in the table and closes the form.
- **Edit** opens the correct row, including when two markers have the same name. A valid save updates the row and closes the form. An invalid save shows the error and retains the entered values.
- **Delete** removes only the clicked row. Deleting the last marker restores the empty message, and deleting the marker currently being edited closes its form. Saved timestamps still drive the Overview cutoff.
