# Usage data model

SQLite stores the first four classes. Requests and measurements live in memory for each report. Store timestamps in UTC at source precision so any saved timestamp can serve as a cutoff. Use the dashboard time zone for date selection and display.

## Class overview

| Class | Description |
| --- | --- |
| <a name="collectedcodexrecord"></a>`CollectedCodexRecord` | Preserves one JSONL line byte for byte, including any terminator. |
| <a name="codexagentthread"></a>`CodexAgentThread` | Identifies an execution by separate session and thread IDs, with an optional verified parent. |
| <a name="codexusage"></a>`CodexUsage` | Records token counts for a response or legacy counter delta. |
| <a name="timemarker"></a>`TimeMarker` | Stores a named timestamp across rebuilds and schema upgrades. |
| <a name="statsrequest"></a>`StatsRequest` | Carries report filters, time range, and grouping settings. |
| <a name="usagemeasurement"></a>`UsageMeasurement` | Summarizes usage and coverage for a reporting window or a group within it. |

`CodexUsage` has nullable input, output, cached input, cache-write input, reasoning output, and total token counts.

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
