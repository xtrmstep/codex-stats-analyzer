## Title

Preserve original Codex log records locally

## Goal

Keep the original data available for future changes to the parser or usage model, even when Codex moves or removes the source logs.

## Work

- Implement [`CollectedCodexRecord`](../specification/02-architecture/02-design/010-usage-data-model.md#collectedcodexrecord), [`CodexLogReader`](../specification/02-architecture/02-design/020-backend-class-design.md#codexlogreader), [`DatabaseWriter`](../specification/02-architecture/02-design/020-backend-class-design.md#databasewriter), and the collection portion of [`CodexLogImporter`](../specification/02-architecture/02-design/020-backend-class-design.md#codexlogimporter). Define the initial versioned SQLite schema and place the generated database in the existing ignored `data/` directory.
- Follow the [raw collection workflow](../specification/02-architecture/02-design/030-collection-and-accounting.md#raw-collection). Provide a source-ordered read of committed raw records for replay.
- Reuse source configuration in `app.py` and applicable discovery logic in `parser.py`. The existing `parser.ingest()` opens files and decodes JSON in one pass. Extract the byte-reading path so collection can retain lines the parser cannot interpret.

## Acceptance Criteria

- Original bytes and provenance are available for supported, unknown, malformed, and incomplete lines. Identical lines at different source positions remain distinct.
- Reimporting the same files or a verified archive copy preserves record identity and counts. Appending lines or completing a final line preserves the verified existing bytes. A rewrite or truncation with uncertain continuity preserves the prior records.
- Missing source files leave collected records available. A failed per-source write leaves its previous records intact and returns a diagnostic. Source logs are unchanged.
- Focused checks demonstrate that records can be read from SQLite with the original files unavailable.
- `DatabaseWriter` uses a supplied destination mapping and supports transactional writes without depending on a Codex record type.
