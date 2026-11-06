# 10 — Run creation UI and complete dashboard integration

Status: Not started | Phase: 2 | Dependencies: 06, 08, 09

Specification: §§5, 6; MVP 5–7, 9, 13.

## Scope

- Add run creation from a selected session, accepting an entire session, timestamps, or start/end events from the timeline.
- Provide run editing/deletion, metadata forms, notes, outcome and optional evaluation score, with validation and clear save feedback.
- Add a detailed runs table with sorting, grouping, filtering and bulk label assignment.
- Complete dashboard KPIs with run count and average/median tokens per run; add run/label breakdowns and all specified global filters.
- Explain overlapping runs and multiple-label categories where group totals are not additive. Show manual labels alongside, but distinct from, detected skill/agent evidence.

## Acceptance and validation

- Exercise creation and editing of each boundary type, multiple runs within one session, bulk labels and restart persistence.
- All dashboard charts and tables respond consistently to the complete filter set.
- Validate displayed run metrics against task 09 fixtures and preserve unknown versus zero distinctions.
