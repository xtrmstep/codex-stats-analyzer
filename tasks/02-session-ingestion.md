# 02 — Read-only session discovery and normalized events

Status: Implementation complete; independent review pending | Phase: 1 | Dependencies: 01

Specification: §§2.1–2.2, 3.1–3.2, 8; MVP 1, 11, 13.

## Scope

- Inspect representative local event formats read-only; create sanitized or synthetic fixtures for supported variants.
- Discover JSONL files under active, archived, and configured directories, including nested folders. Avoid duplicate imports when roots overlap or sessions appear in multiple sources.
- Normalize session ID, project path, timestamps, model, reasoning effort, agent identifiers, role/nickname, token counters, and coordination/skill evidence into records with source provenance.
- Define stable event references using native identifiers where available and a documented deterministic fallback. References must survive restart, appends, and movement to archives.
- Handle missing directories, empty files, unknown event types, malformed lines and partially written final lines without discarding valid records. Report parsing diagnostics without inventing missing fields.

## Acceptance and validation

- Fixtures cover supported shapes, missing fields, malformed input, duplicate discovery, appends and archive relocation.
- Repeated imports produce stable identities and no duplicated events.
- Original file contents and modification times remain unchanged; unsupported data is reported rather than silently interpreted as valid usage.

## Decisions and validation evidence

- Sampled the top-level event and payload key shapes from five local files without recording their contents. Supported explicit structures include session metadata, turn context, response items, token-count events and token-usage records; unfamiliar top-level event types are diagnosed.
- Session metadata IDs are preferred; files without one use the filename as a fallback. References combine that identity, any event ID, a canonical event content hash and the occurrence count of identical content within a file. Copies with the same session and content are deduplicated; source path and line remain provenance. Renaming a file without a session ID changes its fallback identity, and divergent or reordered copies cannot always be reconciled.
- Inline synthetic checks covered nested overlapping roots, missing and empty directories, malformed and partial lines, unknown events, counters, repeated imports, append stability, archive relocation, duplicated copies, and unchanged source bytes and modification time. No unit-test files were added.
- Independent review is pending.

- Review fixes: inline malformed-record checks confirmed non-string event types and escaped lone surrogates are diagnosed while later valid events remain available. A synthetic nested `source.subagent.thread_spawn` session confirmed parent ID, role and nickname propagate to later events without treating conversation text as evidence. Python compilation passed after each fix; independent re-review remains pending.
