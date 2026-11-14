## Title

Display Overview usage in fixed chronological order

## Specification

Follow the [Overview configuration and breakdown behavior](../specification/01-screens/030-content.md#3222-trends-and-charts). This task has no new implementation prerequisites.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), remove the **Sort by** selectbox and **Sort order** radio from the Overview configuration. Remove their local variables and arguments from the `render_statistics()` call. Keep **Refresh sources**, **Time aggregation**, and **Usage view** in the same block.
- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), remove `sort_by` and `sort_order` from `render_statistics()` and delete the configurable sorting branches. For **Project over time** and **Agent over time**, order the measurements within each scope by `UsageMeasurement.bucket` before `_row()` formats it. Put absent buckets last. Use case-insensitive project or agent names as the secondary key, with the original spelling as a final tie-breaker. Use the existing bucket values from [`usage_statistics.py`](../src/internal/analytics/usage_statistics.py) without changing bucket calculation or timestamp handling. For **Agent by project**, use project then agent name. For **Model**, use the model name, which the measurement exposes through `agent` and `_row()` puts in the `Model` column. Compare names case-insensitively with an exact-name tie-breaker and handle missing names consistently.
- Build the per-scope breakdown table and CSV rows from that ordered sequence. Keep the summary row first for each scope, with **Full selected period** before **Since [marker]**. Make the trend chart's `Time` axis chronological even when Plotly splits the data into multiple project or agent traces. A date axis preserves the spacing of dated buckets. If the chart includes an unknown bucket, use an explicit chronological category order with **Unknown** at the end. Keep existing chart types, series, token values, and hover fields.
- Keep the Overview breakdown table in the prescribed order when users interact with column headers. Prefer retaining `st.dataframe` with Streamlit's supported column-selection mode, which disables column sorting. Verify the interaction in the app and preserve the ability to scroll the breakdown. [Streamlit `st.dataframe` reference](https://docs.streamlit.io/1.55.0/develop/api-reference/data/st.dataframe)
- Remove any references left unused by this change. The current sort branches have no dedicated imports or dependencies. Keep sidebar filters and their option ordering, agent naming, marker behavior, calculations, KPI and component displays, and CSV fields. Keep changes within the Overview renderer and its caller.

## Acceptance Criteria

- The Overview offers neither **Sort by** nor **Sort order**. Clicking the breakdown table headers leaves rows in their prescribed order.
- Both time-based views show recorded buckets oldest to newest at hourly, daily, weekly, and monthly granularity. In both reporting windows, chart position, table rows, and CSV breakdown rows follow the same bucket order even when one series starts later than another, a later bucket uses more tokens, or the groups were returned out of order. Rows sharing a bucket have deterministic name order, and any unknown bucket follows dated buckets.
- **Agent by project** and **Model** keep stable name order. The CSV retains its existing columns and scope summary rows. Filters, marker cutoffs, totals, time aggregation, and empty states behave as before.
