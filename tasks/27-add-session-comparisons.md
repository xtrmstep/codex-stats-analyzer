## Title

Add session comparisons to Overview

## Dependencies

- Task 25 provides the Overview results area and removes the run-based comparison panel.

## Work

- Add a section within Overview for the [session comparisons](../specification/01-screens/030-content.md#session-comparisons) specified for two or more session groups. Use the available filters and observed execution characteristics. Keep Overview and Manual annotations as the two navigation entries.
- Calculate comparisons from the same committed session and usage data used by Overview. The existing `src/internal/ui/experiment_ui.py` and `src/internal/metadata/experiments.py` compare runs. Reuse applicable presentation and coverage-aware calculations while defining group membership and metrics by session.
- Show the specified group table, aggregate bars, token-distribution box plots, and calculable absolute and percentage differences. Show coverage and flag known differences that affect comparability.

## Acceptance Criteria

- Users can compare at least two session groups without creating runs or labels. Counts and metrics describe sessions and use the published data available to Overview.
- The comparison shows the required table and charts. Missing or unverifiable measurements remain unknown, and group differences are presented as observations.
