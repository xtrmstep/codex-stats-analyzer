# 14 — Windows offline acceptance and documentation

Status: Validation and documentation in progress; independent review pending | Phase: 3 | Dependencies: 01–13

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
- A hidden local Streamlit server using a process-only synthetic profile responded `ok` at its local health endpoint. An independent browser check loaded synthetic dashboard charts and the run editor, and downloaded session CSV matching 180 total, 150 input and 30 output tokens with coverage and UTC provenance. No real source configuration was changed. The 1280×720 browser view clipped KPI text containing partial-coverage suffixes; correction is pending.
- A complete browser workflow for label/run/comparison editing, refresh and all CSV downloads has not been exercised. Runtime with networking unavailable, absence of remote browser asset requests, fresh offline launch from the space-containing path, and no-auth operation with network physically disabled remain unverified. Do not treat this task as release acceptance yet.

## MVP evidence and limitations

| Criterion | Evidence and remaining validation |
|---|---|
| 1. Discover and parse sessions | Synthetic integrated discovery passed; unsupported shapes and incomplete lines remain diagnostic. |
| 2. Accurate tokens without double-counting | Synthetic increments and overlap union passed; parent/child counter scope remains unresolved and affected totals are withheld or partial. |
| 3. Subagent relationships and roles | Explicit nested parent/role synthetic hierarchy passed; not all observed coordination variants are supported. |
| 4. Hierarchy and breakdown | Synthetic hierarchy passed and dashboard charts loaded; broader interactive hierarchy checks remain. |
| 5. Create and label runs | Synthetic storage and assignment passed; browser editor displayed; complete interactive save/restart remains. |
| 6. Whole-session and interval runs | Synthetic run calculations and earlier boundary checks passed; root-thread-only coverage is explicitly partial. |
| 7. Filters | Synthetic combined filter and earlier task checks passed; complete interactive cross-filter validation remains. |
| 8. Comparison groups | Synthetic two-group calculation and prior three-group roundtrip passed; full browser workflow remains. |
| 9. Local metadata | Synthetic annotation/experiment reload passed; complete application restart workflow remains. |
| 10. Refresh and CSV | Synthetic refresh/export passed and browser session CSV matched displayed fixture; run/comparison downloads and full browser refresh remain. |
| 11. Preserve sources | Synthetic source hashes and modification times were unchanged after reads. |
| 12. Offline/no authentication | Local synthetic launch succeeded without entering credentials; network-disconnected runtime and asset checks remain. |
| 13. Observed/manual/estimated distinctions | Synthetic records and UI labels retain provenance; browser review of the complete workflow remains. |

- Follow-up KPI fix: numeric KPI values no longer include long coverage suffixes; a separate caption reports complete, partial or unknown for each metric. Inline checks verified compact and unknown values and preserved table formatting; compilation passed. Browser verification is pending.
