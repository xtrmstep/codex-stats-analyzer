## Title

Filter Overview usage by agent name

## Specification

Follow the [Agent filter](../specification/01-screens/010-navigation.md#15-filters) and [reporting name rules](../specification/01-screens/030-content.md#3222-trends-and-charts). This task has no code dependency on task 36 or on the Chat filter.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), use the existing eligible thread set derived from date, project, model, and observed role selections. Populate **Agent** with distinct reporting names and **All agents**. Use a separate internal value for **All agents** so the default is independent of the displayed text. Preserve a selected name while eligible and reset to **All agents** before rendering when the name becomes unavailable.
- Reuse the reporting-name logic in [`usage_statistics.py`](../src/internal/analytics/usage_statistics.py). Expose the existing `_agent()` as a named function callable by the two agent calculators and the Overview. Preserve its precedence of `assigned_name`, `agent_name`, `role`, and `Default`. Match equal reporting names across all eligible executions and resolve the selection to their stable execution IDs. Keep different spellings as distinct names.
- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), pass the optional execution-ID set through to `StatsRequest.agents`. Preserve the meaning of `None` as unrestricted and an empty set as matching nothing. In `dashboard.py`, replace the single-execution lookup used to narrow the observed-event frame with membership in the selected executions' `(session_id, thread_id)` pairs. Use the same resolved selection for the frame and the report. Retain usage with no verified owner in unrestricted reports.
- Remove the Overview's use of `execution_labels()`. Keep the helper and the existing individual-execution labels and edits in [`agent_names_ui.py`](../src/internal/ui/agent_names_ui.py). Preserve title import, parent relationships, the observed role filter, and the existing metrics, marker windows, and CSV format.

## Acceptance Criteria

- Two executions named **Reviewer** in different chats produce one **Reviewer** option. Selecting it includes both executions in both reporting windows, subject to the other criteria.
- Named subagents use the same reporting-name precedence as the charts. A verified nameless execution appears under **Default**. Agent options contain only names and the default control label.
- Changing other filters preserves an eligible Agent selection and clears an ineligible one. Role filtering still uses the recorded role. Manual annotations still identifies and edits individual executions.
