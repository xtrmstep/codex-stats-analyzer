## Title

Calculate statistics for the previous period

## Specification

Follow the [reporting windows specification](../specification/01-screens/030-content.md#reporting-windows). This task prepares the comparison data for tasks 64 and 65.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), add a small helper that derives the previous bounds from the resolved inclusive dates. The comparison starts `day_count` days before the selected start and ends one day before it, where `day_count = (end - start).days + 1`. Return no bounds for **All Time**.
- Prepare the comparison using the selected chat title and agent reporting name. Match those selections against the threads in the existing reporting snapshot, including matching executions absent from the selected period. Preserve the current sidebar options and selected-period execution IDs. Leave the comparison unrestricted by execution ID when both selections are unrestricted. An active selection with no matching executions uses an empty set.
- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), prepare an optional comparison result for the renderers. When comparison bounds are supplied, derive a second `StatsRequest` from the selected-period request with those dates, the comparison execution IDs, and `marker=None`. Reuse the same `StatsCalculation` instance and keep its returned summary and chart groups with the comparison dates. Keep the selected and marker results on the original request. The next tasks will render the result and supply the bounds when the checkbox is on.

## Acceptance Criteria

- **Today** produces yesterday. October 12–18 produces October 5–11. Verify inclusive boundaries across a leap day and a year boundary, and verify a partial **Current month** uses the resolved span length.
- The comparison uses the same project, model, role, chat, and agent selections and the same time aggregation. A matching execution found only in the previous dates contributes to the comparison. The saved marker affects only its own result.
- With no comparison bounds, there is no second calculation. When bounds exist but no usage matches, the normal calculator returns unavailable values and empty chart groups without substituting zero.
