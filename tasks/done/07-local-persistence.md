# 07 — Atomic local metadata storage

Status: Complete; independent review passed | Phase: 2 | Dependencies: 01, 02

Specification: §§2.3–2.5, 5.3, 7.4, 8; MVP 9.

## Scope

Review: independent Astra re-review passed at `d55aee7`; combined replacement/cleanup failure verified with independent lock release.

- Define versioned schemas for `data/annotations.json` (labels, assignments, runs and metadata) and `data/experiments.json` (comparison definitions and any agreed history representation).
- Reference stable sessions/events independently of source file locations; tolerate temporarily missing source sessions without deleting annotations.
- Validate reads and writes. Save through a temporary file and atomic replacement in the same directory; ensure failures preserve the previous valid file.
- Define handling for unsupported schema versions, corrupt JSON and competing writes. Never silently overwrite unreadable metadata with an empty store.
- Keep persistence in the small file-based application structure.

## Acceptance and validation

- Round-trip Unicode labels, run boundaries and comparison definitions across restart.
- Failure-injection checks verify interrupted/failed saves preserve the prior valid data.
- Missing source records, corrupt JSON and version mismatches produce actionable diagnostics without data loss.

## Decisions and validation evidence

- Version 1 annotations contain `labels`, `assignments` and `runs` arrays. Entries use stable string IDs; assignments reference label IDs and a session or run ID; runs carry a stable session ID and may retain boundary and metadata fields. Experiment documents contain an `experiments` array with IDs, names, groups and metrics. Additional JSON fields are retained to support later workflows; definitions are not tied to source paths. Missing source sessions are reported by `missing_sessions` without deletion. Experiment history is not recorded yet; task 12 must define its semantics.
- Missing files load as unsaved empty documents; corrupt files and unknown versions fail without replacement. Saves use a same-directory temporary file, flush/fsync, and atomic replacement. A content-hash revision plus an exclusive lock file protects cooperating writers; stale locks are never automatically removed and require inspection. External programs that ignore the lock cannot be serialized by this protocol. A changed revision requires reload before saving.
- Inline synthetic checks passed Unicode labels, event boundaries and experiment definitions after reload; missing-source detection; stale-revision and lock conflicts; injected replacement failure with previous bytes intact; and corrupt/version-mismatch read and save preservation. Python compilation passed. Independent review pending.

- Review fix: injected simultaneous replacement and temporary-file deletion failures preserved original bytes, reported both failures, and released the lock. Compilation passed; independent re-review pending.
