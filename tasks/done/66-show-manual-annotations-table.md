## Title

List saved time markers on Manual Annotations

## Specification

Follow the [Manual Annotations page](../specification/01-screens/030-content.md#34-manual-annotations). The date and time pickers are covered by task 67.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), rename the navigation label and matching page branch to **Manual Annotations**. Add the matching page heading and remove the `agent_name_editor()` call and import. Remove the agent-name editor module if it has no remaining callers. Keep stored assignments and their use in Overview reporting.
- In `marker_editor()` in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), remove the old **Saved time markers** heading and reuse the `list_markers()` result to show a read-only table above the existing editor. Show **Name** and **Local date and time**. Convert the saved offset-bearing timestamps for display in the app's local zone and sort by instant. Keep the existing create, edit, and delete actions keyed by marker ID.
- Show **No saved time markers** for an empty list and keep the create form available. Use the existing reruns after writes to refresh the table.

## Acceptance Criteria

- The navigation and page heading read **Manual Annotations**. The page shows the saved marker list and editor. Existing assigned agent names still appear in the Overview where applicable.
- Each saved marker appears once, including markers sharing a name. Dates and times show in the app's local zone in chronological order. Creating, editing, or deleting a marker updates the list, including the empty state after the last deletion.
