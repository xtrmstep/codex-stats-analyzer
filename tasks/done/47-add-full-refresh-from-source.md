## Title

Replace imported data with a full source refresh

## Specification

Follow [full refresh and publication rules](../specification/02-architecture/02-design/000-system-overview.md#component-behavior). This task is confined to the importer and does not require the new UI.

## Work

- In [`collection.py`](../src/internal/ingestion/collection.py), add `CodexLogImporter.full_refresh(roots)` with the same `(success, diagnostics)` result as `refresh()`. Use the configured roots and chat-title index, read every discovered log from its beginning, and reuse reader discovery, byte collection, archive-move handling, and registered transformations. Start with empty source mappings so prior checkpoints cannot skip files. Save fresh checkpoints from successful reads when checkpoint support is present.
- Replace the imported dataset atomically in SQLite. Reuse the existing collection and rebuild operations with an outer transaction for this path. Factor transaction ownership out of internal steps as needed so a nested `BEGIN` or an early commit cannot expose a partial reset. Replace `published_logs`, `usage_records`, `coverage_diagnostics`, `agent_threads`, `chat_title_evidence`, `source_paths`, `collected_records`, `logs`, and the import state in foreign-key-safe order. Commit the new evidence manifest and derived rows together. Keep `time_markers`, `agent_names`, and other user-authored data out of the reset. Preserve the execution ID rule in [`transformations.py`](../src/internal/ingestion/transformations.py) so assignments still apply when the corresponding execution is reimported.
- Report missing roots and continue with available logs. A missing optional title index leaves the new title evidence empty. An actual enumeration, log read, index read, transformation, or write failure prevents publishing a replacement. Check that at least one original source line was loaded before committing. Keep malformed or incomplete lines under the existing diagnostic rules. Ensure fatal diagnostics returned by shared helpers trigger rollback before returning the failure result. Rollback preserves the prior archive and report.
- Keep `refresh()` incremental and `rebuild()` available for reprocessing records from SQLite. Leave the original Codex source files, application settings, and usage calculations as they are.

## Acceptance Criteria

- Full refresh rereads all discovered logs, including ones with unchanged file metadata. After success, previously imported records absent from source and their derived results are gone. Raw replay and report data describe the same replacement snapshot. Saved markers and agent names persist.
- Verify a fatal collection failure, a failed transformation or write, and a scan with no source records. Each leaves the prior archive, checkpoints, and publication available. A missing optional root with other readable logs yields a warning and imports those logs.
- Incremental refresh still retains history and resumes from the current source state. The existing SQLite-only rebuild still works without source files.
