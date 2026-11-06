# 09 — Run definitions and interval metrics

Status: Implementation complete; independent review pending | Phase: 2 | Dependencies: 03, 04, 07

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

## Decisions and validation evidence

- A run has a stable ID, session ID, name, optional description/task metadata/outcome/score/notes, and a boundary of `whole_session`, `timestamps` or `events`. Legacy records without a boundary default to whole session; legacy `boundaries` objects remain stored but cannot be calculated until explicitly converted. Missing sources/events and invalid or out-of-range boundaries do not erase annotations or produce zero usage.
- Intervals use half-open [start, end) endpoints. Timestamp bounds require explicit timezone offsets and must lie within observed session timestamps. Event bounds use stable references and source order, including equal-time events. Untimestamped increments cannot be allocated to timestamp intervals. Counter observations are attributed by event timestamp or position; usage may span boundaries, so interval totals are estimates marked partial. Whole-session runs expand on refresh. Root-thread usage only is included: child counters may overlap parent counters and are not added. Overlapping runs can be unioned by source reference without duplication.
- Timestamp-boundary elapsed is a manual interval; event-boundary and whole-session elapsed use observed spans, not verified execution duration. Missing or out-of-order endpoint timestamps yield unknown elapsed. Labels continue to use task 08 assignments and inheritance.
- Inline synthetic checks passed whole-session totals, adjacent intervals, equal-time ordering, root-only child exclusion, overlapping unions, invalid/missing/out-of-range boundaries, untimestamped increments and persisted event references. Python compilation passed. Independent review pending.

