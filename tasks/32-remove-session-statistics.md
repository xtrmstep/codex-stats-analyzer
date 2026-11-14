## Title

Remove session-based reporting

## Goal

Keep session and thread identities in the imported data for attribution and traceability. Base Overview statistics on time, projects, models, and agents.

## Work

- In `src/internal/ui/dashboard.py`, remove the **Sessions** filter, **Session** usage view, session table and download, **Session detail** panel (including its embedded hierarchy and timeline), and session comparison panel. In `src/internal/ui/statistics_ui.py` and `src/internal/ui/exports.py`, remove session counts, grouping fields, and session-only export columns from the active reports. Keep the agent count.
- In `src/internal/analytics/usage_statistics.py`, remove `SessionUsageCalculator`, its registration, `StatsRequest.sessions`, and the session count in `UsageMeasurement`. Retain the internal session/thread lookup used to attribute observed events and count distinct agents. Remove the session selection from the Overview filter path in `src/internal/analytics/metrics.py` and `statistics_ui.py`. Check remaining callers before changing shared legacy filter fields. Saved marker scope is handled separately in task 33.
- Update the [sidebar](../specification/01-screens/010-navigation.md#15-filters), [content](../specification/01-screens/030-content.md), [system overview](../specification/02-architecture/02-design/000-system-overview.md), and [backend class design](../specification/02-architecture/02-design/020-backend-class-design.md) to describe the supported reports and internal use of session identity. Remove obsolete session reporting instructions from `README.md`.

## Acceptance Criteria

- Overview has no session filter, grouping, count, detail, comparison, or session CSV. The remaining usage CSV has no session field.
- Usage from different chats can contribute to the same project, model, or named-agent group under the existing accounting rules. Preserve imported IDs, parent links, source references, per-execution accounting, project attribution, and the remaining controls and reports.
