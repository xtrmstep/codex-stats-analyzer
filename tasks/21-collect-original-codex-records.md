## Title

Preserve original Codex log records locally

## Goal

Keep the original data available for future changes to the parser or usage model, even when Codex moves or removes the source logs.

## Work

- Implement `CollectedCodexRecord`, `CodexLogImporter`, and the raw record operations in `UsageStore` using Python's `sqlite3` and a versioned schema.
- Follow the [data model and raw collection design](../specification/02-architecture/02-design/000-system-overview.md#raw-collection). Keep collection independent of parsing and accounting. Expose a source-ordered read for the usage builder.
- Reuse configured source directories and the existing file discovery behavior where applicable.

## Acceptance Criteria

- Original bytes and provenance are available for supported, unknown, malformed, and incomplete lines. Identical lines at different source positions remain distinct.
- Reimporting the same files or a verified archive copy preserves record identity and counts. Appending lines or completing a final line preserves the verified existing bytes. A rewrite or truncation with uncertain continuity preserves the prior records.
- Missing source files leave collected records available. A failed per-source write leaves its previous records intact and returns a diagnostic. Source logs are unchanged.
- Focused checks demonstrate that records can be read from SQLite with the original files unavailable.
