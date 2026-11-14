## Title

Use named time markers across chats

## Work

- In `src/internal/ui/statistics_ui.py`, remove **Chat scope**, the chat picker, and their session lookup. Keep the marker name, timestamp, and create, edit, select, and delete actions.
- In `src/internal/analytics/usage_statistics.py`, remove chat scope from `TimeMarker` and the marker read and save operations. In `StatsCalculation.calculate()`, remove the separate marker session restriction from usage and observed-agent selection. Both windows use the same active report filters. **Since [name]** adds the inclusive time cutoff within the selected date range. Keep the stored timestamp format and existing coverage and empty-window behavior. Limit persistence changes to marker scope in `src/internal/ingestion/collection.py` where necessary.
- Update the [manual annotations specification](../specification/01-screens/010-navigation.md#122-manual-annotations), [reporting windows](../specification/01-screens/030-content.md#reporting-windows), and [marker data model](../specification/02-architecture/02-design/010-usage-data-model.md#timemarker) to define a named timestamp with no chat criterion.

## Acceptance Criteria

- A marker named **Switched to multi-agent** can be saved and edited with its timestamp and appears by name in Overview. Both reporting windows apply to the same filtered population across chats, and the marker changes only the time cutoff.
- Marker creation and editing do not require any published chats. Refresh and rebuild preserve saved names and timestamps. Existing date and offset behavior stays in place.
