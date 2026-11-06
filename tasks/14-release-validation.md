# 14 — Windows offline acceptance and documentation

Status: Not started | Phase: 3 | Dependencies: 01–13

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
