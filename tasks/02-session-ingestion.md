# 02 — Read-only session discovery and normalized events

Status: Not started | Phase: 1 | Dependencies: 01

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
