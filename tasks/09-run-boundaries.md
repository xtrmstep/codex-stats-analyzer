# 09 — Run definitions and interval metrics

Status: Not started | Phase: 2 | Dependencies: 03, 04, 07

Specification: §§2.3, 5.2–5.3; MVP 5, 6, 13.

## Scope

- Model multiple runs per session using whole-session, timestamp-boundary and stable event-boundary selection.
- Store name, description, labels, task identifier, task type, outcome (success/failure/partial/unknown), optional evaluation score and notes.
- Define interval endpoint inclusivity, equal-time event ordering, invalid boundary behavior, child-agent inclusion, and whether whole-session runs expand when new events arrive.
- Attribute token increments from available event timing; document the treatment of increments spanning boundaries and mark estimated results explicitly.
- Calculate each run independently, while preventing overlapping runs from inflating session/global usage totals. Preserve missing values and partial attribution.
- Derive elapsed time with its provenance; do not equate a first/last activity span with verified active execution time.

## Acceptance and validation

- Fixtures cover whole sessions, adjacent/overlapping intervals, equal timestamps, empty intervals, missing events, out-of-range boundaries, and subagent activity.
- Run metrics reconcile with the accounting model under the declared policy; boundary uncertainty remains visible.
- Stable references and metadata survive source refresh, archive movement and application restart.
