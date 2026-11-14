## Title

Transform collected Codex records into stored usage

## Goal

Produce agent thread and usage records from the retained logs so the reporting layer can query a committed dataset.

## Dependencies

- [Task 21](./21-collect-original-codex-records.md) provides raw collection, the generic writer, and the SQLite replay reader.

## Work

- Extend `CodexLogImporter` to run the [registered transformations](../specification/02-architecture/02-design/020-backend-class-design.md#codexrecordtransformation) and publish [`CodexAgentThread`](../specification/02-architecture/02-design/010-usage-data-model.md#codexagentthread), [`CodexUsage`](../specification/02-architecture/02-design/010-usage-data-model.md#codexusage), and coverage diagnostics in one transaction. Support collection followed by transformation and a rebuild from SQLite alone.
- Adapt `parser.py` to parse collected lines and preserve separate session, thread, turn, and response identities where supplied. `agents.py` currently keys its hierarchy and usage lookups by session ID. Reuse relationship evidence but resolve a shared owning thread for hierarchy and accounting.
- Update `analytics.py` to use per-response usage where supported. Its existing cumulative deltas are grouped by session before attribution. Preserve counter validation and compute legacy deltas within verified owner streams. Follow the [rebuild and accounting rules](../specification/02-architecture/02-design/030-collection-and-accounting.md#usage-rebuild-and-accounting) for overlap and unknown coverage.
- Preserve existing session and event references used by annotations and run boundaries, or provide a compatibility mapping where identities change.

## Acceptance Criteria

- Rebuilding after removing access to the original logs yields the same results from the same collected records. Duplicate or overlapping evidence is accounted for according to the specification.
- A failed collection or transformation leaves the last committed derived dataset available and reports the failure. A successful rebuild preserves collected records and user-authored data.
- The two registered transformations run through the same importer contract. Reporting can query committed usage and threads with attributable model, project, and coverage information.
