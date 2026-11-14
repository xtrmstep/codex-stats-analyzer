## Title

Preserve original Codex log records locally

## Goal

Keep the original data available for future changes to the parser or usage model, even when Codex moves or removes the source logs.

## Work

- Implement [`CollectedCodexRecord`](../specification/02-architecture/02-design/010-usage-data-model.md#collectedcodexrecord), [`CodexLogReader`](../specification/02-architecture/02-design/020-backend-class-design.md#codexlogreader), [`DatabaseWriter`](../specification/02-architecture/02-design/020-backend-class-design.md#databasewriter), and the collection portion of [`CodexLogImporter`](../specification/02-architecture/02-design/020-backend-class-design.md#codexlogimporter). Define the initial versioned SQLite schema and place the generated database in the existing ignored `data/` directory.
- Follow the [raw collection workflow](../specification/02-architecture/02-design/000-system-overview.md#raw-collection). Provide a source-ordered read of committed raw records for replay.
- Reuse source configuration in `app.py` and applicable discovery logic in `parser.py`. The existing `parser.ingest()` opens files and decodes JSON in one pass. Extract the byte-reading path so collection can retain lines the parser cannot interpret.

## Acceptance Criteria

- Original bytes and provenance are available for supported, unknown, malformed, and incomplete lines. Identical lines at different source positions remain distinct.
- Reimporting the same files or a verified archive copy preserves record identity and counts. Appending lines or completing a final line preserves the verified existing bytes. A rewrite or truncation with uncertain continuity preserves the prior records.
- Missing source files leave collected records available. A failed per-source write leaves its previous records intact and returns a diagnostic. Source logs are unchanged.
- Focused checks demonstrate that records can be read from SQLite with the original files unavailable.
- `DatabaseWriter` uses a supplied destination mapping and supports transactional writes without depending on a Codex record type.

## Issue Logs

### Failed check 1

- `collection.py` requires a database path with no default in `data/`. Archive matching consults only current path mappings, so a rewritten source can hide the earlier generation from a later archive copy.
- The task requires the generated database in `data/` and stable identity for verified archive copies while retaining rewritten records.
- Provide the specified default location and include historical record provenance when matching archive copies.

### Failed check 2

- `CodexLogReader.replay()` orders by each record's source path before its log identity and line number. Lines appended after an archive move can therefore precede earlier lines of the same log.
- The task requires a source-ordered replay of committed raw records.
- Group replay by log identity and order its records by line number.

### Failed check 3

- `CodexLogImporter.collect()` reads a source before acquiring its SQLite write transaction. Concurrent imports can process an older snapshot after a newer one and mistake it for a truncation.
- This risks assigning a new identity to an unchanged source and violates stable reimport behavior.
- Acquire the per-source write transaction before reading the source and checking continuity.

### Failed check 4

- `CodexLogReader.read_source()` returns bare bytes, while replay returns records with explicit source paths and line numbers.
- The backend design requires source and replay reads to expose original lines with source positions through the same reader interface.
- Return positioned source-line objects with the same provenance and byte attributes used by replay records.

### Failed check 5

- `collection.py` uses the complete path below `sessions` or `archived_sessions` as the archive matching key. An active log in date subdirectories and its verified copy directly in `archived_sessions` have different keys and are collected twice.
- This violates the criterion that a verified archive copy preserves record identity and counts.
- Match archive candidates using supported source identity and verified bytes even when directory layouts differ, while preserving distinct unrelated logs and handling ambiguous matches conservatively.

### Unresolved summary

Archive matching assumes identical relative directory layouts. Codex archives can use a different layout, so the current implementation cannot reliably identify every verified archive copy. Revise candidate matching and verify flat archives, multiple candidates, rewrites, and byte-prefix continuity before completing the task.
