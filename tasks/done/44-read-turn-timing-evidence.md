## Title

Read verified turn timing evidence from committed records

## Specification

Provide the inputs required by the [turn throughput rule](../specification/02-architecture/02-design/020-backend-class-design.md#token-accounting). This parser task is independent of the KPI help and renderer.

## Work

- In [`parser.py`](../src/internal/ingestion/parser.py), extend `_normalize()` and the existing event evidence path for the logged `event_msg` subtypes `task_started` and `task_complete`. Preserve the outer recorded timestamp and existing `turn_id`, execution identity, and `record_id` in `parse_collected()`. Retain `duration_ms` from completion as numeric evidence, and retain a failure indicator when the completion reports an error. Recognize `turn_aborted` as contradictory terminal evidence for the same turn. Use the existing evidence container and leave other event handling unchanged.
- Keep absent or invalid duration distinguishable from zero. Do not infer a duration from token counter observations or use time to first token for this calculation. Read the existing committed original records. Keep the SQLite schema, imports, and token accounting unchanged. The report will match and validate the timing evidence in task 45. [Codex lifecycle event source](https://github.com/openai/codex/blob/main/codex-rs/core/src/tasks/mod.rs)

## Acceptance Criteria

- A replay exposes start and completion timing for the same verified execution and turn, with the original timestamps and a valid duration in milliseconds. Aborted, failed, malformed, and missing timing cases can be distinguished from a valid successful completion.
- Existing event normalization, original record replay, and usage counts are unchanged. Timing is available through the report's committed snapshot even when the source files are absent.
