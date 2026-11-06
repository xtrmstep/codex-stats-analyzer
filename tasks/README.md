# Implementation task plan

Source of truth: [Codex Usage Analyzer specification](../specification/codex-usage-analyzer.md), preserved as supplied on 2026-11-06.

Progress: Tasks 01–10 are implemented and independently reviewed; Task 11 is active; Tasks 12–14 are not started. Review commit references are recorded in each task file. Interactive browser/offline asset validation remains for task 14. Task numbers give the recommended execution order. Dependencies are prerequisites, and each task includes concrete completion checks.

Execution override: the user authorized local-only Git work while no remote is available. Each task branch builds on the preceding reviewed task; remote discovery and pushes are deferred.

Keep the application small: Python, Streamlit, pandas, Plotly, JSON/JSONL, and local files. Do not introduce external databases, plugin frameworks, distributed components, or background services. Runtime must work offline without authentication; installation may download dependencies. Document an offline installation path using locally supplied dependencies.

## Phase 1 — Reliable analytics

| Task | Deliverable | Depends on |
|---|---|---|
| [01](01-foundation.md) | Application skeleton, configuration, Windows launchers | — |
| [02](02-session-ingestion.md) | Read-only discovery, parsing, stable references | 01 |
| [03](03-token-accounting.md) | Auditable token increments and aggregates | 02 |
| [04](04-agent-evidence.md) | Agent relationships and skill evidence | 02, 03 |
| [05](05-analytics-filters.md) | Shared metrics and filter semantics | 03, 04 |
| [06](06-dashboard.md) | Overview, session detail, hierarchy and timeline | 05 |

Phase gate: fixture-backed accounting is reliable, source files remain unchanged, and the overview and session detail agree under available filters. Label/run filters are completed in Phase 2.

## Phase 2 — Annotations and runs

| Task | Deliverable | Depends on |
|---|---|---|
| [07](07-local-persistence.md) | Atomic annotations and experiments storage | 01, 02 |
| [08](08-labels.md) | Label management, bulk assignment and filtering | 05, 07 |
| [09](09-run-boundaries.md) | Run definitions, interval attribution and metadata | 03, 04, 07 |
| [10](10-run-workflows.md) | Run UI and full dashboard integration | 06, 08, 09 |

Phase gate: labels and runs survive restart, all dashboard views use the selected filters, and interval estimates and unknown data are visible.

## Phase 3 — Experiment comparison

| Task | Deliverable | Depends on |
|---|---|---|
| [11](11-experiment-analytics.md) | Group filters, comparison metrics and caveats | 05, 08, 09 |
| [12](12-experiment-ui.md) | Saved comparisons and all comparison charts | 07, 10, 11 |
| [13](13-refresh-export.md) | Refresh consistency and CSV export | 06, 10, 12 |
| [14](14-release-validation.md) | Offline Windows validation and user documentation | 01–13 |

Phase gate: saved experiments recalculate after refresh, exports agree with the UI, and all MVP criteria pass on Windows offline.

## MVP acceptance traceability

| Specification §10 criterion | Tasks |
|---|---|
| 1. Discover and parse sessions | 02, 14 |
| 2. Accurate tokens without double-counting | 03, 05, 09, 14 |
| 3. Subagent relationships and roles | 04, 14 |
| 4. Hierarchy and session breakdown | 04, 06 |
| 5. Create and label runs | 08–10 |
| 6. Whole-session and interval runs | 09, 10 |
| 7. All statistics respect filters | 05, 08, 10–12 |
| 8. Multiple comparison groups | 11, 12 |
| 9. Local annotations and comparisons | 07–10, 12 |
| 10. Refresh and CSV export | 13 |
| 11. Preserve source files | 02, 13, 14 |
| 12. Offline, no Codex authentication | 01, 14 |
| 13. Observed/manual/estimated distinctions | 02–06, 09–12, 14 |

## Decisions to settle during implementation

Record decisions alongside the relevant task before implementing dependent behavior. These are unresolved semantics, not changes to the supplied specification:

- Task 02: actual supported event shapes, fallback identifiers, and duplicate-source identity.
- Tasks 03–04: counter scopes, reset handling, parent rollup behavior and reliable agent/skill evidence.
- Tasks 05, 08–09: timezone and interval endpoint policy, filter composition, label inheritance, overlapping runs, and agent inclusion in runs.
- Tasks 07 and 12: schema evolution and experiment-history representation within the specified JSON files.
- Task 11: eligible denominators, elapsed-time confidence, baseline selection and zero-baseline differences.

Use synthetic or sanitized fixtures for tests. Keep private session content out of the repository and preserve provenance so results can be traced to source events. Each implementation task should include its relevant tests; task 14 validates the complete workflow rather than deferring all testing until release.
