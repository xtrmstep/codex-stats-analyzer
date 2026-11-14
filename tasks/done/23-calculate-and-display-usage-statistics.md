## Title

Calculate and display usage statistics from SQLite

## Goal

Report usage by project and time, agent and time, and agent and project. Compare the selected period with the part of that period since a saved marker.

## Dependencies

- [Task 22](./22-build-and-report-stored-usage.md) provides the committed usage dataset, thread attribution, and importer entry points.

## Work

- Implement [`StatsCalculation` and the three calculators](../specification/02-architecture/02-design/020-backend-class-design.md#statistics-classes) with [`StatsRequest`](../specification/02-architecture/02-design/010-usage-data-model.md#statsrequest) and [`UsageMeasurement`](../specification/02-architecture/02-design/010-usage-data-model.md#usagemeasurement). Reuse applicable filtering and aggregation in `metrics.py`, whose existing functions take event and increment frames and group by a single dimension at a time.
- Persist [`TimeMarker`](../specification/02-architecture/02-design/010-usage-data-model.md#timemarker) through the generic writer and implement [marker management](../specification/01-screens/030-content.md#saved-time-markers) and the [reporting windows](../specification/01-screens/030-content.md#reporting-windows).
- Wire `app.py` and `dashboard.py` to invoke the importer on first use and source refresh and use committed data for reporting. `dashboard.render()` currently invokes `ingest()`, `calculate_increments()`, and `build_dataset()` on every render. Replace that path for the usage views. Preserve existing session labels, run and experiment behavior, and session detail. Use stored raw records for existing features that still need parsed events or increments.
- Make dashboard charts, summaries, and relevant `exports.py` paths consume the same measurements. Show the effective period for each scope as defined in the [content specification](../specification/01-screens/030-content.md#322-metrics).

## Acceptance Criteria

- All three views read committed usage and share filters, token accounting, and coverage rules across charts, summaries, and exports. A filter or marker change does not read original log files.
- First use initializes the usage dataset and **Refresh sources** imports subsequent changes. If refresh fails, the dashboard shows the diagnostic alongside the last usable report.
- Selecting a saved marker shows both scopes, including their own totals, weighted cache percentage, daily average, and coverage. Empty intersections and legacy intervals crossing a cutoff follow the product specification.
- A report uses a consistent committed dataset if refresh completes while calculations are running. Measurements are returned in memory and markers survive refresh and restart.

## Issue Logs

### Failed check 1

- The current overview replacement omits the specified input/output distribution and model/session breakdowns, and session/agent counts include only threads with stored usage rows. It also does not explain when potentially overlapping legacy counters were withheld.
- The screen specification requires those views and counts alongside coverage-aware accounting, and the task requires consistent measurements across the dashboard and exports.
- Derive the omitted views and observed counts from the same committed snapshot and display the overlap explanation alongside affected summaries.

### Failed check 2

- The new overview does not display processing speed or independently attributable subagent share, both required by the content specification.
- This leaves required overview metrics unavailable even when the report can identify independently attributable subagent responses.
- Display unknown processing speed when duration evidence is unavailable and calculate subagent share only for scopes with verified independent usage and hierarchy.

### Failed check 3

- Time-bucket measurements inherit uncertainty only from the overall reporting cutoff. A legacy delta can cross a bucket boundary while the bucket is incorrectly displayed as complete. The usage CSV also omits several token components shown or retained by the report.
- The specification requires bucket bounds to be clipped to the reporting window, uncertain legacy attribution to be flagged, and exports to use the same measurements as the dashboard.
- Mark deltas spanning a bucket boundary partial and include the retained token components in exported measurements.

### Failed check 4

- `runs.calculate_run()` selects every event and increment with the run's session ID. Replayed records can contain several agent threads in one session, so child-thread activity can enter a run described as root-thread-only.
- The task requires existing run behavior to be preserved while using stored raw records.
- Resolve a unique observed root thread from verified hierarchy evidence, restrict run boundaries and increments to it, and report unknown attribution when the root is ambiguous.
- `metrics.build_dataset()` also carries project, model, and role by session, so a child thread can inherit a sibling's filter context. Carry context by thread when replayed records provide one.

### Failed check 5

- `dashboard.render()` and `StatsCalculation` replay the current `collected_records`, while `CodexLogImporter.refresh()` can commit earlier raw sources before a later source fails and leaves the previous derived dataset in place. A failed refresh can therefore combine older committed usage with newer raw events in session counts and details.
- The task requires the last usable report after a failed refresh and a consistent committed dataset throughout each report.
- Publish an immutable raw-record snapshot together with derived usage and diagnostics, then read reporting events, counts, and usage from that same committed generation. Preserve previously published bytes when an incomplete raw line is later extended.

### Unresolved summary

Raw collection commits per source, whereas derived publication commits separately. The reporting path currently reads the latest raw collection independently of the derived generation. A failed or concurrent refresh can therefore mix generations. Persist a raw snapshot or equivalent generation-aware immutable evidence in the derived publication transaction, then verify failed-refresh, incomplete-line extension, and concurrent-read scenarios before completing the task.

### Resolution

Each successful publication now commits per-log line and byte boundaries with the derived data. Reports read the manifest, derived rows, diagnostics, and bounded raw evidence from one SQLite snapshot. Transactional version upgrades rebuild unmanifested data before enabling reports. Focused checks cover partial refresh failure, final-line extension, SQLite-only rebuild, concurrent readers and initialization, schema migration, and initial failure.

### Follow-up verification

- All-time report bounds were derived only from usage rows, omitting earlier observed activity without counters from the daily-average period.
- The rate specification includes days with no recorded usage when coverage is complete.
- Derive open-ended report bounds from both eligible observed events and eligible usage rows in the same publication.
- Session-detail calculations also resolved open-ended bounds independently, allowing their displayed periods to drift from the overview. Reuse the overview's resolved bounds for those calculations.
- When a marker precedes an open-ended period's first observation, the marker scope started before the selected period. Clip it to the resolved period start.
- The new-marker form generated a fresh default timestamp on every rerun, causing a submitted timestamp to be replaced by the current time. Keep the initial default stable for the session and verify the saved timestamp.
- When both reporting scopes contain identical data, Streamlit assigns duplicate chart IDs and stops rendering. Give each scope's charts distinct stable keys.
- Marker actions trigger a Streamlit rerun before the database connection is closed, leaving SQLite handles open. Close the connection in a `finally` block on every render exit.

### Follow-up resolution

Open-ended bounds now include eligible observed activity and are reused for detail calculations. Marker scopes are clipped to the resolved period. The marker form keeps a stable initial timestamp, scope charts have distinct keys, and dashboard database connections close on rerun. Focused Streamlit checks verified the entered and edited marker timestamps, identical scope charts, failed-refresh fallback, and connection cleanup.
