## Title

Add chat scope to manual events

## Dependencies

- Task 25 provides the Manual annotations view and the Overview marker selector.

## Work

- Add **All chats** and **Selected chats** to the existing event editor according to the [navigation specification](../specification/01-screens/010-navigation.md#122-manual-annotations). In selected mode, let the user choose sessions from the published dataset and require at least one session. Store stable session IDs and load existing markers as all-chat events.
- Pass the event scope through the existing marker model and statistics request in `src/internal/analytics/usage_statistics.py`. Use a compatible database upgrade for saved marker data. Preserve stored session selections when sessions are temporarily unavailable and show their unavailable status when editing.
- Keep both [reporting windows](../specification/01-screens/030-content.md#reporting-windows). Apply the active Overview filters to both. For **Since [event]**, additionally apply the inclusive cutoff and intersect the active session selection with any chats selected on the event. Keep **Full selected period** as the baseline for the active Overview filters.

## Acceptance Criteria

- Users can create, edit, and delete events from Manual annotations. Existing markers retain their behavior. A saved scope survives restart and source refresh.
- Selecting an all-chat event adds the cutoff to the second window. Selecting a scoped event limits that window to the matching chats. The baseline still reflects the active Overview filters.
- Charts, tables, and CSV agree on the effective event scope. Empty matches remain visible and do not broaden to all chats.
