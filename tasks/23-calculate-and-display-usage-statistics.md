## Title

Calculate and display usage statistics from SQLite

## Goal

Report usage by project and time, agent and time, and agent and project. Compare the selected period with the part of that period since a saved marker.

## Dependencies

- [Task 22](./22-build-and-report-stored-usage.md) provides the committed usage dataset, thread attribution, and importer entry points.

## Work

- Implement [`StatsCalculation` and the three calculators](../specification/02-architecture/02-design/020-backend-class-design.md#statistics-classes) with [`StatsRequest`](../specification/02-architecture/02-design/010-usage-data-model.md#statsrequest) and [`UsageMeasurement`](../specification/02-architecture/02-design/010-usage-data-model.md#usagemeasurement). Reuse applicable filtering and aggregation in `metrics.py`, whose existing functions take event and increment frames and group by a single dimension at a time.
- Persist [`TimeMarker`](../specification/02-architecture/02-design/010-usage-data-model.md#timemarker) through the generic writer and implement [marker management](../specification/codex-usage-analyzer.md#54-saved-time-markers) and the [reporting windows](../specification/codex-usage-analyzer.md#63-visualizations).
- Wire `app.py` and `dashboard.py` to invoke the importer on first use and source refresh and use committed data for reporting. `dashboard.render()` currently invokes `ingest()`, `calculate_increments()`, and `build_dataset()` on every render. Replace that path for the usage views. Preserve existing session labels, run and experiment behavior, and session detail. Use stored raw records for existing features that still need parsed events or increments.
- Make dashboard charts, summaries, and relevant `exports.py` paths consume the same measurements. Show the effective period for each scope as defined in the [content specification](../specification/01-screens/030-content.md#322-metrics).

## Acceptance Criteria

- All three views read committed usage and share filters, token accounting, and coverage rules across charts, summaries, and exports. A filter or marker change does not read original log files.
- First use initializes the usage dataset and **Refresh sources** imports subsequent changes. If refresh fails, the dashboard shows the diagnostic alongside the last usable report.
- Selecting a saved marker shows both scopes, including their own totals, weighted cache percentage, daily average, and coverage. Empty intersections and legacy intervals crossing a cutoff follow the product specification.
- A report uses a consistent committed dataset if refresh completes while calculations are running. Measurements are returned in memory and markers survive refresh and restart.
