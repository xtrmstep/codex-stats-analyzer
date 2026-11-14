## Title

Assign agent names for cross-chat reporting

## Dependencies

- Tasks 32 and 33 remove session-based reports and the marker chat picker. Task 34 provides display titles for identifying chats in the agent editor and filter.

## Work

- Add an agent naming control to the Manual annotations view in `src/internal/ui/dashboard.py` or its existing UI helpers. Let users set, edit, and clear a name for an individual execution. Offer recognizable labels using the shared chat title and the agent role or nickname when available. Use a readable fallback for an untitled chat and a display-only disambiguator where labels repeat. Keep IDs as internal option values. Use the same readable labels in the **Agent** filter, which still selects individual executions. Keep the **Agent roles** filter tied to the observed role.
- Keep assignments in local user metadata keyed by stable execution ID, separate from imported `agent_threads`. Read assignments with the report data in `src/internal/analytics/usage_statistics.py`. In `_agent()`, use the assigned name, then recorded name or role, then **Default**. Apply the same rule to both agent calculators and their chart, table, and CSV output. Preserve existing token aggregation, coverage, and Project and Model views.
- Update the [content](../specification/01-screens/030-content.md), [manual annotations](../specification/01-screens/010-navigation.md#122-manual-annotations), and [data model](../specification/02-architecture/02-design/010-usage-data-model.md) to describe assignments and readable identifiers. Leave chat title and project attribution rules unchanged.

## Acceptance Criteria

- Naming two executions **Reviewer** groups their usage together across chats within the same time bucket or project. Clearing an assignment restores the recorded name or role, or **Default** when both are absent. Refresh and rebuild preserve assignments.
- Agent selection and editing show human-readable labels without session or thread IDs. Duplicate chat or agent names remain independently selectable. Renaming an agent execution changes its report group while leaving its role and accounting identity intact.
