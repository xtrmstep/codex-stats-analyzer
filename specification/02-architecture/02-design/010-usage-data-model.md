# Usage data model

SQLite stores the first four classes. Requests and measurements live in memory for each report. Store timestamps in UTC at source precision so any saved timestamp can serve as a cutoff. Use the dashboard time zone for date selection and display.

## Class overview

### CollectedCodexRecord

Preserves the exact bytes of one JSONL line, including any terminator. Log identity survives verified appends and archive moves. See [raw collection](./000-system-overview.md#raw-collection).

### CodexAgentThread

Identifies one execution with separate session and native thread IDs and an optional verified parent. Session ID groups threads when supported by the source. Name or role groups executions across chats, and nickname can identify an execution in the UI.

### CodexUsage

Represents a response or legacy counter delta. Provenance and coverage track potential overlap. Legacy deltas retain the prior observation time when known. Input, output, cached input, cache-write input, reasoning output, and total token counts are nullable.

Match context by thread and turn IDs when available. Take the model from matched context. Use the turn's working directory for project attribution, with the thread's directory as fallback. Keep the source directory and group worktrees by normalized repository identity when known, otherwise by normalized directory. Show missing project, model, or agent attribution as unknown.

### TimeMarker

Stores a user-named timestamp across rebuilds and schema upgrades. See [saved time markers](../../codex-usage-analyzer.md#54-saved-time-markers).

### StatsRequest

Carries report settings, including grouping by execution, name, or role. All calculators share the same filters and resolved [reporting windows](../../codex-usage-analyzer.md#63-visualizations). See [StatsCalculation](./020-backend-class-design.md#statscalculation).

### UsageMeasurement

Reports one on-demand summary or group from committed rows for the full period or since the marker. Values carry complete, partial, or unknown coverage. Empty windows are explicit and unknown amounts stay distinct from zero.

## Class schema

```mermaid
classDiagram
    class CollectedCodexRecord {
        record_id
        log_identity
        source_path
        line_number
        original_line_bytes
        collected_at
    }
    class CodexAgentThread {
        execution_id
        session_id
        thread_id
        parent_execution_id
        agent_name, role, nickname
    }
    class CodexUsage {
        usage_id
        source_record_id
        execution_id
        observed_at, prior_observed_at
        source_working_directory
        project_key, project_label, model
        token_counts, coverage
        counter_provenance
    }
    class TimeMarker {
        marker_id
        name
        timestamp
    }
    class StatsRequest {
        filters
        selected_bounds, time_zone
        time_bucket_size
        agent_grouping
    }
    class UsageMeasurement {
        scope, effective_bounds
        project_key, agent_key, time_bucket
        token_totals, coverage
        cache_percentage, average_daily_tokens
        empty_window
    }
    CodexUsage --> "1" CollectedCodexRecord : source record
    CodexUsage --> "0..1" CodexAgentThread : verified owner
    CodexAgentThread --> "0..1" CodexAgentThread : verified parent
    StatsRequest --> "0..1" TimeMarker : selected marker
```
