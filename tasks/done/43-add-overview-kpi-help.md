## Title

Explain each Overview KPI in the interface

## Specification

Use the labels and explanations in [Overview KPIs](../specification/01-screens/030-content.md#3221-overview-kpis). This UI task is independent of the timing and calculation work.

## Work

- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), add one compact `help=` tooltip to each of the nine `st.metric()` calls in the reporting-window summary. Use the wording in the KPI table. Show **Turn throughput** in the existing processing-speed slot. [Streamlit metric reference](https://docs.streamlit.io/1.55.0/develop/api-reference/data/st.metric)
- Keep the displayed values, `Unknown` handling, units, formatting, and arrangement. Keep the existing agent count caption, charts, filters, and CSV. Leave value calculation to the existing analytics paths and task 45.

## Acceptance Criteria

- All nine metrics have compact explanations in every reporting window that shows KPIs, including when a value is **Unknown**. The explanations are available from the metric help affordance and add no permanent text rows.
- Both reporting windows retain the same values and controls. The throughput slot retains its existing **Unknown** value until the calculation is wired in.
