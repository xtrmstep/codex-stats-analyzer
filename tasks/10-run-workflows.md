# 10 — Run creation UI and complete dashboard integration

Status: Implementation complete; independent review pending | Phase: 2 | Dependencies: 06, 08, 09

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

## Decisions and validation evidence

- Run editor supports whole-session, timezone-aware timestamp and source-order event boundaries, along with description, task ID/type, execution mode, outcome, score, notes and explicit labels. The existing label manager handles bulk run assignments and shows inherited versus explicit labels. Run deletion removes explicit run assignments. Event selectors show timestamps, types and complete stable references.
- Other global filters intersect with session and run classifications. Matching session labels select matching session rows; matching run labels or explicit run selection select attributed interval rows. Their union uses original row identities so overlapping runs and multiple labels do not duplicate global usage. Per-label breakdowns also union rows within each label; different categories may overlap. Run tables and KPI mean/median use known selected run totals only, labeled partial. All run-derived totals remain partial and root-thread-only because child counter scope is unresolved; elapsed reflects the full defined run, not verified execution time.
- Inline synthetic checks passed creating, editing and reloading all three boundary modes; run labels/classification filtering, known run averages/medians, overlap deduplication, root-only partial totals and editor rendering without implicit writes. Modules compiled. Browser interaction and full end-to-end offline UI were not verified in this sandbox; independent review pending.

