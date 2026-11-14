## Title

Associate imported agent threads with their chat title

## Work

- Add a read-only input for the Codex `session_index.jsonl` in the ingestion code. Read `id`, `thread_name`, and `updated_at`. Keep it distinct from the rollout files handled by `CodexLogReader` in `src/internal/ingestion/collection.py`. Retain enough index evidence in SQLite for a rebuild to resolve the same titles without reading the original index again. A missing index or a malformed entry must leave usage import available.
- In `src/internal/ingestion/transformations.py`, resolve the root thread of a session from verified identity evidence. Match that root thread ID to the index and resolve the latest valid title using `updated_at`. Provide one optional title per session to all its executions, including subagents. When no root or title can be resolved unambiguously, leave the title unknown. Keep the import and report snapshot boundaries for the published title data.
- Document the title source and association in the [system overview](../specification/02-architecture/02-design/000-system-overview.md) and [usage data model](../specification/02-architecture/02-design/010-usage-data-model.md). Treat titles as display metadata. Leave project attribution, IDs, role metadata, and token accounting in place.

## Acceptance Criteria

- A root and its subagents resolve to the same chat title. A subagent's index entry does not override its root's chat title. Two chats with the same title retain distinct identities.
- Refresh picks up a valid rename for the whole chat. SQLite-only rebuild reproduces the title from retained evidence. Missing or conflicting title evidence leaves titles unknown without affecting token metrics.
