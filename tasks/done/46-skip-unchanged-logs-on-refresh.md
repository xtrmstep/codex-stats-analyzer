## Title

Skip unchanged log files during incremental refresh

## Specification

Follow [incremental refresh and log continuity](../specification/02-architecture/02-design/000-system-overview.md#component-behavior). This task is limited to incremental collection and can be implemented without the new full refresh or UI actions.

## Work

- In [`collection.py`](../src/internal/ingestion/collection.py), persist nullable file size and `st_mtime_ns` checkpoints on `source_paths` using the existing `DatabaseWriter._initialize_schema()` versioning. Keep current path-to-log mappings and retained records. Treat a path with no verified checkpoint as a normal candidate for a read.
- Keep recursive discovery. Compare the current source metadata against its checkpoint for the resolved path before `CodexLogReader.read_source()` opens the file. Keep the existing read and `_continues()` validation for new or changed paths and the existing `_archive_key()` matching for archive moves. New paths must still be checked even if their metadata matches another path.
- Update the checkpoint in the same per-source transaction as the corresponding bytes. Compare metadata before and after reading. If it changed or cannot be verified, leave that path eligible for a read next time. Preserve the existing error reporting for failed reads. If a write changes the stored byte prefix of a log shared by several path mappings, invalidate any other checkpoint that describes the previous prefix.
- Keep chat-title index collection, raw history retention, derived rebuild, and publication behavior. A checkpoint represents raw capture, so a later retry must still rebuild from the retained raw records when a previous publication failed. Leave the UI unchanged.

## Acceptance Criteria

- After a successful scan, a second scan discovers the same paths but does not open unchanged log files. New files load their full contents, and a normal append adds only new lines. A completed final line keeps its original record ID and full bytes.
- Rewritten and truncated logs retain the existing behavior, and verified archive moves reuse the log identity. A changed file, a file modified during a read, and a path with no checkpoint are eligible for another read. A failed write cannot advance its checkpoint.
- Incremental refresh retains history from missing source files. If a derived rebuild fails after raw capture, retrying publishes the already-captured records even when their files are skipped.
