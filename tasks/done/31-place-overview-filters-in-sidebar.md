## Title

Place Overview filters below sidebar navigation

## Goal

Implement the [sidebar layout](../specification/01-screens/010-navigation.md#15-filters) with persistent Navigation and a Filters section for Overview.

## Work

- In `src/internal/ui/dashboard.py`, keep the existing two-item sidebar navigation. Add a Filters container below it for Overview. Render Projects, Models, Sessions, Agent roles, Agent, and Saved time marker in that container using the existing widget definitions, option sources, and defaults. The specification also lists execution mode. The current Overview has no execution-mode control, so implementing it is outside this placement task.
- Reuse `marker_selector()` from `src/internal/ui/statistics_ui.py` in the sidebar container. Keep `marker_editor()` in the Manual annotations body. Keep the current data-loading order so the retry action is reachable without published data and data-dependent filter options come from committed results.
- Keep the shared date range in the header. Keep Refresh sources, Time aggregation, Usage view, Sort by, and Sort order in the [Overview configuration](../specification/01-screens/030-content.md#321-view-parameters--view-configuration). Keep session detail and comparison group controls next to their results.
- Preserve the values passed into `Filters`, `filter_dataset()`, and `render_statistics()`. Keep project-key selection, agent option narrowing, name-based grouping, marker scope, and reporting windows. Limit edits to widget placement and the container wiring needed for it.

## Acceptance Criteria

- Overview shows Navigation followed by Filters in the sidebar. The relocated controls appear there once. The header still defaults to **All Time**, and the main body shows report controls and results.
- Changing a filter or marker still changes the same results, session details, and exports. Refresh and the last-committed-results fallback retain their behavior.
- Manual annotations shows Navigation and its editor with no Overview filters. Both navigation entries still select their respective views.
