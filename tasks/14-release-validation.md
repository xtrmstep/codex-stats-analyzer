# 14 — Windows offline acceptance and documentation

Status: Partially verified; offline acceptance and independent review pending | Phase: 3 | Dependencies: 01–13

Specification: §§1, 8–11; all MVP acceptance criteria.

## Scope

- Run the task-specific parser, accounting, hierarchy, filter, persistence, run and comparison checks as an integrated suite.
- Exercise a Windows workflow: setup, launch, discovery, agent inspection, run creation, bulk labels, filtered analysis, comparison save/reopen, refresh and CSV export.
- Verify runtime with networking unavailable, no Codex authentication, localhost-only binding, disabled telemetry and no remotely fetched UI assets.
- Verify original source hashes/modification times remain unchanged and all user metadata survives restart.
- Document setup/run commands, Python support, offline dependency installation, source configuration, refresh/export, labels/runs/experiments, file locations and metadata backup/recovery.
- Explain supported source formats, unknown/partial values, estimated boundaries, observed activity versus execution time, overlap semantics and comparison limitations.
- Smoke-check a representative larger local fixture collection and record dataset size/timings; optimize only measured issues without adding architectural complexity.

## Acceptance and validation

- Record evidence for each of the 13 MVP criteria using the mapping in `tasks/README.md`.
- A fresh Windows setup can complete the documented workflow and then operate fully offline.
- No known accounting, persistence or source-integrity failures remain; document actual unsupported source variants and remaining limitations.

## Integrated validation evidence

- Python 3.12 compiled all application modules. Inline synthetic checks exercised discovery, counter deltas, explicit hierarchy, label/run persistence and inheritance, run overlap deduplication, shared filtering, saved comparison reload/recalculation, Unicode CSV quoting and source hash/mtime preservation. The checks created no permanent test files.
- A 100-file synthetic collection with 10,000 events and 9,900 increments produced 19,900 analytics rows in 0.596 seconds for ingestion, accounting and frame construction on this machine. This is a smoke check, not a performance guarantee.
- A fresh Python 3.12 environment was installed successfully from a locally prepared wheelhouse using `--no-index` in a project path containing spaces. The wheelhouse was prepared online; physical network disconnection was not tested.
- A hidden local Streamlit server using a process-only synthetic profile responded `ok` at its local health endpoint. An independent browser check loaded synthetic dashboard charts and the run editor, and downloaded session CSV matching 180 total, 150 input and 30 output tokens with coverage and UTC provenance. No real source configuration was changed. The initial 1280×720 browser view clipped KPI text; the subsequent compact-value fix was visually verified at a narrow viewport.
- The isolated browser exercised label assignment, whole-session run creation, saved comparison/history, refresh and session/run/comparison CSV downloads. Editing every boundary type and every cross-filter combination, fresh offline launch from the space-containing path, browser-level network blocking, and operation with the machine physically disconnected remain unverified. Inspected page asset references were local or relative, but this was not a complete network audit. Do not treat this task as release acceptance yet.

## MVP evidence and limitations

| Criterion | Evidence and remaining validation |
|---|---|
| 1. Discover and parse sessions | Synthetic integrated discovery passed; unsupported shapes and incomplete lines remain diagnostic. |
| 2. Accurate tokens without double-counting | Synthetic increments and overlap union passed; parent/child counter scope remains unresolved and affected totals are withheld or partial. |
| 3. Subagent relationships and roles | Explicit nested parent/role synthetic hierarchy passed; not all observed coordination variants are supported. |
| 4. Hierarchy and breakdown | Synthetic hierarchy passed and dashboard charts loaded; broader interactive hierarchy checks remain. |
| 5. Create and label runs | Synthetic storage and assignment passed; browser created and labeled two runs, and they persisted across restart. |
| 6. Whole-session and interval runs | Synthetic run calculations and earlier boundary checks passed; root-thread-only coverage is explicitly partial. |
| 7. Filters | Synthetic combined filter and earlier task checks passed; complete interactive cross-filter validation remains. |
| 8. Comparison groups | Synthetic two-group calculation and prior three-group roundtrip passed; browser saved and reopened a two-group comparison and its history after restart. |
| 9. Local metadata | Synthetic annotation/experiment reload passed; isolated browser confirmed runs and a saved comparison with history after application restart. |
| 10. Refresh and CSV | Synthetic refresh/export passed; browser refresh and session/run/comparison downloads were exercised and checked against fixture values. |
| 11. Preserve sources | Synthetic source hashes and modification times were unchanged after reads. |
| 12. Offline/no authentication | Local synthetic launch succeeded without entering credentials; network-disconnected runtime and asset checks remain. |
| 13. Observed/manual/estimated distinctions | Synthetic records and UI labels retain provenance; browser review of the complete workflow remains. |

- Follow-up KPI fix: numeric KPI values no longer include long coverage suffixes; a separate caption reports complete, partial or unknown for each metric. Inline checks verified compact and unknown values and preserved table formatting; compilation passed. Narrow-viewport browser verification passed.

- Additional isolated browser validation: a separate synthetic app copy used its own empty metadata and a Python-process guard denying non-loopback DNS and socket connections. The browser created and bulk-assigned one label to alpha/beta/child, saved two whole-session runs, saved and reopened a two-group comparison, recorded one history point, clicked refresh, and downloaded run/comparison CSV. Readback confirmed run totals 180/100 and group means 180/100. The filtered alpha view showed 180 total, 150 input, 30 output, 33.3% cache and one run; compact KPI values were readable at the checked narrow viewport. Inspected script/link/image references were local or relative. The persisted comparison names were Group 1 and Group 2, with Group 1 as baseline.
- The isolated server was restarted with the same data under the guard; all three source hashes and mtimes matched immediately before and after restart. After restart, the browser showed two persisted runs with average and median 140 and reopened the saved comparison with its group filters and history trend. The guard covers only the Python process, not browser or operating system networking; physical network disconnection and a browser-level network block remain unverified.

