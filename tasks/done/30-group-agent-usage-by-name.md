## Title

Group agent usage reports by name

## Goal

Use agent names as the fixed grouping for **Agent over time** and **Agent by project** so separate threads for the same agent appear together.

## Work

- In `src/internal/ui/dashboard.py`, remove the **Agent grouping** radio and its argument at the `render_statistics()` call. Keep the separate **Agent** filter and its thread-level selection behavior.
- In `src/internal/ui/statistics_ui.py`, remove the `grouping` parameter from `render_statistics()` and stop passing it into `StatsRequest`. Keep charts, tables, and CSV using the grouped measurements they already receive.
- In `src/internal/analytics/usage_statistics.py`, remove `StatsRequest.agent_grouping` and replace the switch in `_agent()` with its existing name logic. In `AgentUsageOverTimeCalculator` and `AgentUsageByProjectCalculator`, always use the recorded `agent_name`, falling back to `role`. Keep the existing unknown group when neither is available. Names that match group together within each time bucket or project. Keep the current treatment of nicknames.
- Update the [content specification](../specification/01-screens/030-content.md#3222-trends-and-charts) and [backend class design](../specification/02-architecture/02-design/020-backend-class-design.md#statistics-classes) to describe name grouping in the two agent reports. Remove `agent_grouping` from the `StatsRequest` diagram in the [usage data model](../specification/02-architecture/02-design/010-usage-data-model.md#statsrequest). Keep grouping controls that serve other purposes.

## Acceptance Criteria

- Both agent reports group rows by the recorded name or role and expose the same group names in charts, tables, and CSV. Two threads named Developer share the same group within one bucket or project and remain separate across different buckets or projects as applicable. Unknown names and roles appear under **Unknown**.
- The **Agent grouping** radio is absent. The **Agent** filter still selects individual threads. Thread identity, counts, hierarchy, session details, coverage, and counter overlap rules remain intact.
- Project, Model, and Session breakdowns, marker windows, filters, time buckets, and sorting retain their behavior. No database, import, or schema changes are needed.
