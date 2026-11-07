# 06 — Overview and session analysis UI

Status: Complete; independent code review passed | Phase: 1 | Dependencies: 05

Specification: §§4, 6; MVP 4, 7, 13.

## Scope

Review: independent Astra review passed at `9175775`; mixed timestamps, filtered activity, and unrelated skill exclusion checked. Interactive browser/offline asset validation remains for task 14.

- Create a Streamlit overview with global filters and available KPIs; add run-related controls and KPIs in task 10.
- Render Plotly token trends at daily/weekly/monthly resolution, project/model/session breakdowns, cached versus non-cached input, and main versus subagent usage.
- Provide a sortable, filterable, grouped session table and a session detail view.
- Show the detected hierarchy, unlinked agents, per-agent metrics, and a Gantt-style activity timeline. Selecting an agent filters relevant usage charts.
- Distinguish recorded activity spans from verified durations and show parsing/coverage limitations alongside affected values.

## Acceptance and validation

- With a known fixture dataset, chart totals, table totals and KPIs agree under each supported filter.
- Verify main-only, nested-agent, unlinked-agent, empty and partial-data views.
- Check interactive charts render offline and display observed facts and estimates with clear labels.

## Decisions and validation evidence

- The overview and session detail use task 05 filters and shared summaries for KPIs, breakdowns, time buckets and agent usage. UTC date controls, project/model/session/role selections and a selected-agent control intersect. Session hierarchy and activity spans show full evidence as context; usage metrics and charts follow active filters. Unknown and partial amounts are labeled, and main/subagent figures are not added when scope may overlap.
- Inline synthetic rendering with a Streamlit stub exercised populated and empty sources, partial and unknown token KPIs, Plotly chart construction, and a project-filtered KPI/session table reconciliation. Python modules compiled. The Streamlit AppTest attempt stalled in this sandbox and was interrupted; interactive browser rendering, full filter interaction, offline browser assets, and synthetic nested-agent timeline presentation remain unverified. Independent review pending.

- Review fixes: Plotly timeline accepts mixed fractional and non-fractional UTC timestamps and excludes invalid endpoints. Inline nested-agent/date-filter checks using real Plotly confirmed the timeline includes only matching child events and explicit skills exclude unrelated sessions; full hierarchy remains labeled context. Verified intervals are withheld under date filters because their boundaries may extend beyond selection. Compilation passed. Interactive browser/offline assets remain unverified because AppTest stalled; independent re-review pending.
