# 06 — Overview and session analysis UI

Status: Not started | Phase: 1 | Dependencies: 05

Specification: §§4, 6; MVP 4, 7, 13.

## Scope

- Create a Streamlit overview with global filters and available KPIs; add run-related controls and KPIs in task 10.
- Render Plotly token trends at daily/weekly/monthly resolution, project/model/session breakdowns, cached versus non-cached input, and main versus subagent usage.
- Provide a sortable, filterable, grouped session table and a session detail view.
- Show the detected hierarchy, unlinked agents, per-agent metrics, and a Gantt-style activity timeline. Selecting an agent filters relevant usage charts.
- Distinguish recorded activity spans from verified durations and show parsing/coverage limitations alongside affected values.

## Acceptance and validation

- With a known fixture dataset, chart totals, table totals and KPIs agree under each supported filter.
- Verify main-only, nested-agent, unlinked-agent, empty and partial-data views.
- Check interactive charts render offline and display observed facts and estimates with clear labels.
