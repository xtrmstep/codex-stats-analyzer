# 07 — Atomic local metadata storage

Status: Not started | Phase: 2 | Dependencies: 01, 02

Specification: §§2.3–2.5, 5.3, 7.4, 8; MVP 9.

## Scope

- Define versioned schemas for `data/annotations.json` (labels, assignments, runs and metadata) and `data/experiments.json` (comparison definitions and any agreed history representation).
- Reference stable sessions/events independently of source file locations; tolerate temporarily missing source sessions without deleting annotations.
- Validate reads and writes. Save through a temporary file and atomic replacement in the same directory; ensure failures preserve the previous valid file.
- Define handling for unsupported schema versions, corrupt JSON and competing writes. Never silently overwrite unreadable metadata with an empty store.
- Keep persistence in the small file-based application structure.

## Acceptance and validation

- Round-trip Unicode labels, run boundaries and comparison definitions across restart.
- Failure-injection checks verify interrupted/failed saves preserve the prior valid data.
- Missing source records, corrupt JSON and version mismatches produce actionable diagnostics without data loss.
