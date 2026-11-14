## Title

Transform collected Codex records into stored usage

## Goal

Produce agent thread and usage records from the retained logs so the reporting layer can query a committed dataset.

## Dependencies

- [Task 21](./21-collect-original-codex-records.md) provides raw collection, the generic writer, and the SQLite replay reader.

## Work

- Extend `CodexLogImporter` to run the [registered transformations](../specification/02-architecture/02-design/020-backend-class-design.md#codexrecordtransformation) and publish [`CodexAgentThread`](../specification/02-architecture/02-design/010-usage-data-model.md#codexagentthread), [`CodexUsage`](../specification/02-architecture/02-design/010-usage-data-model.md#codexusage), and coverage diagnostics in one transaction. Support collection followed by transformation and a rebuild from SQLite alone.
- Adapt `parser.py` to parse collected lines and preserve separate session, thread, turn, and response identities where supplied. `agents.py` currently keys its hierarchy and usage lookups by session ID. Reuse relationship evidence but resolve a shared owning thread for hierarchy and accounting.
- Update `analytics.py` to use per-response usage where supported. Its existing cumulative deltas are grouped by session before attribution. Preserve counter validation and compute legacy deltas within verified owner streams. Follow the [token accounting rules](../specification/02-architecture/02-design/020-backend-class-design.md#token-accounting) for overlap and unknown coverage.
- Preserve existing session and event references used by annotations and run boundaries, or provide a compatibility mapping where identities change.

## Acceptance Criteria

- Rebuilding after removing access to the original logs yields the same results from the same collected records. Duplicate or overlapping evidence is accounted for according to the specification.
- A failed collection or transformation leaves the last committed derived dataset available and reports the failure. A successful rebuild preserves collected records and user-authored data.
- The two registered transformations run through the same importer contract. Reporting can query committed usage and threads with attributable model, project, and coverage information.

## Issue Logs

### Failed check 1

- The initial transformation does not yet reconcile disjoint response and legacy scopes, propagate source-level coverage gaps to affected usage, or update the existing hierarchy and accounting entry points. Conflicting source identity also needs conservative handling during replay.
- The task requires correct accounting and coverage for all supported records, consistent owning-thread attribution, and compatibility with existing callers.
- Complete owner resolution and overlap handling, carry diagnostics into coverage, and update existing entry points while preserving their interfaces.

### Failed check 2

- The mixed-stream path combines earlier legacy counters with responses based on file order alone, and legacy cache-write counters are dropped. Token records with a conflicting source session can also be assigned a separate execution without reporting the conflict.
- The specification allows combined usage only for verified disjoint scopes, requires available token components to be preserved, and requires ambiguous attribution to remain unknown.
- Verify a strict timestamp boundary before combining legacy and response records, preserve cache-write increments, and withhold conflicting source ownership with a diagnostic.

### Failed check 3

- `UsageTransformation` groups response observations by session, thread, and response. Conflicting session claims for the same thread and response can therefore be counted twice instead of being recognized as ambiguous.
- The specification requires deduplication by thread and response and excludes ambiguous ownership from verified totals.
- Identify conflicting session claims for a thread, withhold their attribution and report the affected evidence, and deduplicate verified responses by thread and response.

### Failed check 4

- `parse_collected()` inherits the source thread's parent, role, and nickname for a token record explicitly owned by a different thread. The importer also does not validate rows against a transformation's declared output type.
- The task requires hierarchy and accounting to use the same verified owner and both transformations to run through the specified contract.
- Withhold source-thread metadata from foreign or unresolved owners and enforce each registered transformation's output type before publication.

### Failed check 5

- `transformations.py` combines raw parent candidates with hierarchy analysis after that analysis has removed cycles, allowing cyclic parent links to be stored. Its context also retains a session-level repository URL after a turn changes working directory, which can attribute usage to the wrong project.
- The specification requires verified parent relationships and project attribution that prefers the turn's working directory.
- Apply cycle detection to the final parent graph and use repository identity only where it is verified for the applicable working directory.

### Unresolved summary

The derived dataset can contain cyclic hierarchy links and incorrect project attribution after a working-directory change. The likely causes are independent parent-link assembly and carrying repository context across directories without verifying its scope. Reconcile the final hierarchy with the existing cycle handling and associate repository identity with a verified directory before completing this task.
