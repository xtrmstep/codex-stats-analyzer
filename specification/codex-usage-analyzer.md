# Codex Usage Analyzer — Updated Specification

## 1. Purpose

Build a lightweight, fully local Windows application for analyzing Codex token consumption, agent activity, and efficiency across different execution configurations.

The primary use cases are:

- Understand token consumption by session, project, model, and agent.
- Analyze multi-agent execution and subagent overhead.
- Identify which skills were used, where possible.
- Manually classify sessions and task runs.
- Compare different execution configurations.
- Evaluate whether using skills, subagents, or different models improves efficiency.

The application must work without Codex authentication, API access, external services, or network connectivity.

## 2. Core concepts

### 2.1 Session

A Codex conversation identified by its session ID.

A session can contain multiple user requests, execution phases, and agent threads. A thread identifies an individual execution within a session. See the [usage data model](./02-architecture/02-design/010-usage-data-model.md#codexagentthread) for thread identity rules.

### 2.2 Agent

An individual agent participating in an execution.

Types:

- Main agent
- Subagent
- Nested subagent

Where available, capture agent ID, parent agent, model, role, execution timestamps, and token consumption.

### 2.3 Run

A user-defined unit of work.

A run can represent:

- An entire session.
- A particular task within a session.
- A manually selected time interval within a session.

Each run has a name, optional description, start/end boundaries, and labels.

This is the main unit for comparing experiments. Several runs can exist within one session.

### 2.4 Labels

User-defined metadata that can be assigned to sessions or individual runs.

Examples:

| Category | Values |
|---|---|
| Execution mode | single-agent, multi-agent |
| Skills | enabled, disabled |
| Workflow | developer-only, developer-reviewer |
| Task type | coding, specification, review |
| Configuration | baseline, experiment-v1 |
| Result | successful, failed, partial |

Users can create arbitrary additional labels.

Labels support both free-form tagging and structured key/value classification.

### 2.5 Experiment

A saved comparison between two or more groups of labeled runs.

For example:

- Group A: Coding tasks without skills.
- Group B: Coding tasks with skills.
- Group C: Coding tasks with skills and subagents.

An experiment defines its group filters and selected metrics.

## 3. Data collection

### 3.1 Sources

Read local Codex session files from:

- `%USERPROFILE%\.codex\sessions`
- `%USERPROFILE%\.codex\archived_sessions`
- Additional configured directories

Read source JSONL files without modifying them. Preserve their original records locally so usage can be rebuilt after the source files are moved or removed. See [Raw collection](./02-architecture/02-design/030-collection-and-accounting.md#raw-collection).

### 3.2 Extracted information

Collect:

- Session ID and project path
- Event timestamp
- Model and reasoning effort
- Agent and parent-agent identifiers, when available
- Agent role and nickname, when available
- Token counters
- Agent coordination events, when available
- Skill invocation evidence, when available

Never treat mentions of a skill or subagent in ordinary conversation text as proof of actual usage.

### 3.3 Token accounting

Calculate consumption from recorded response usage and supported legacy counter deltas. Apply the [rebuild and accounting rules](./02-architecture/02-design/030-collection-and-accounting.md#usage-rebuild-and-accounting) before grouping or filtering usage.

Track:

- Total tokens
- Input tokens
- Cached input tokens
- Cache-write input tokens, if available
- Non-cached input tokens
- Output tokens
- Reasoning output tokens, if available
- Cache percentage

Support allocation by time, project, session, agent, model, and run.

Ensure that hierarchical rollups do not double-count subagent usage.

Missing statistics must remain unknown rather than being treated as zero.

## 4. Agent analysis

### 4.1 Agent hierarchy

For each session, display the available agent tree:

Main Agent
- Developer Agent
- Reviewer Agent
- Specification Agent
  - Research Agent

The tree must reflect detected parent-child relationships.

Show unlinked agents separately when relationships cannot be reconstructed.

### 4.2 Agent metrics

For each agent, display:

- Model
- Role
- Parent agent
- Token consumption
- Cached input percentage
- First and last recorded activity
- Available execution status

For the complete session, additionally calculate:

- Number of participating agents
- Maximum hierarchy depth
- Main agent token consumption
- Combined subagent token consumption and subagent share where independent usage can be established

### 4.3 Execution timeline

Show a Gantt-style timeline with the main agent and subagents.

Highlight overlapping activity where supported by event timestamps.

Allow selecting an agent to filter the usage charts.

Distinguish observed activity intervals from verified execution durations.

## 5. Manual annotations

### 5.1 Label management

Provide a UI for:

- Creating, editing, and deleting labels
- Assigning multiple labels to a session
- Assigning labels to individual runs
- Applying labels to multiple selected sessions or runs
- Filtering by combinations of labels

### 5.2 Run creation

Allow creating a run from a selected session.

The user can choose:

- Entire session
- Start and end timestamps
- Start and end events from a session timeline

For example, a user might mark:

- 10:00–10:15 — Development without skills
- 10:15–10:30 — Development using skills
- 10:30–10:45 — Development with reviewer agent

The application calculates metrics independently for each interval.

Usage is attributed using available event timestamps. Results from interval boundaries are estimates when exact usage timing is unavailable.

### 5.3 Manual metadata

Each run may include:

- Name
- Description
- Labels
- Task identifier
- Task type
- Outcome: success, failure, partial, unknown
- Optional evaluation score
- Notes

Manual annotations persist across application restarts.

### 5.4 Saved time markers

Users can save, rename, change, and delete a named timestamp such as **Switched to multi-agent**. A marker is available across usage views and persists through application restarts and source rebuilds. Selecting it enables the second reporting window described under [Visualizations](#63-visualizations).

## 6. BI dashboard

### 6.1 Global filters

- Date range
- Project
- Model
- Session
- Agent role
- Labels
- Task type
- Execution mode

All dashboard visualizations respond to selected filters.

### 6.2 Overview KPIs

Display:

- Total tokens
- Input/output token distribution
- Cache percentage
- Sessions
- Runs
- Agents
- Average and median tokens per run
- Average tokens per day
- Subagent token share where independent usage can be established

### 6.3 Visualizations

Provide:

1. Token usage over time, with daily/weekly/monthly aggregation.
2. Token consumption by project, model, session, run, or label.
3. Cached versus non-cached input distribution.
4. Main-agent versus subagent token consumption.
5. Agent hierarchy and execution timeline.
6. Detailed sessions and runs table.

Support sorting, grouping, filtering, and CSV export.

Support token usage by project over time, by agent over time, and by agent and project. Agent views can show individual threads or group executions by observed agent name or role. Include unclassified usage under unknown where attribution is unavailable and the usage can be counted safely.

For each usage view, show metrics for the full selected time range and, when a marker is selected, a second set for the intersection of that range with the time starting at the marker. Both sets use the same project, agent, model, and other active filters. Include observations at the marker timestamp. When the intersection is empty, display **No time in range**. Flag uncertain attribution when a legacy delta spans the cutoff and use its observation time for placement.

Compute average tokens per day over each window's elapsed duration in days, including days with no recorded usage when coverage is complete. Carry the total's coverage status into the average and leave the average unknown when the duration or token total is unavailable. Calculate cache percentage from eligible summed cached input and input tokens in each window.

## 7. Experiment comparison

### 7.1 Creating comparisons

Users select two or more groups using labels and filters.

Example:

Group A:
- Task type: coding
- Skills: disabled
- Execution mode: single-agent

Group B:
- Task type: coding
- Skills: enabled
- Execution mode: single-agent

Group C:
- Task type: coding
- Skills: enabled
- Execution mode: multi-agent

### 7.2 Comparison metrics

| Metric | Purpose |
|---|---|
| Number of runs | Sample size |
| Average tokens per run | Overall consumption |
| Median tokens per run | Typical consumption |
| Cached input percentage | Context reuse |
| Output tokens | Generated token volume |
| Subagent token share | Delegation overhead |
| Elapsed time | End-to-end duration |
| Success rate | Outcome comparison |
| Evaluation score | Quality comparison, if entered |

For token and duration metrics, display absolute differences and percentage differences between groups.

### 7.3 Comparison visualizations

- Grouped bar charts for aggregate metrics
- Box plots for consumption distribution
- Trend charts for experiment history
- Table comparing all selected groups

Show the number of runs in every group.

Flag comparisons where task types, models, or other important conditions differ.

The dashboard reports differences without automatically claiming that one configuration caused them.

### 7.4 Saved experiments

Allow users to save a comparison configuration, including its name, group definitions, filters, and metrics.

Saved experiments can be reopened and recalculated when new runs become available.

## 8. Data storage

The [usage analytics backend](./02-architecture/02-design/000-system-overview.md) stores original collected records, derived usage, and saved time markers in local SQLite. Original Codex JSONL files are read-only. The usage dataset can be rebuilt from the collected records while preserving those records and user-authored data. The [statistics calculations](./02-architecture/02-design/020-backend-class-design.md#statistics-classes) read the committed dataset and produce measurements on demand.

Existing `annotations.json` and `experiments.json` files continue to hold their user-authored data. Preserve stable session and event references and save annotation files atomically.

No external database or server is required.

## 9. Technology

- Python
- Streamlit — dashboard UI
- pandas — data analysis
- Plotly — interactive charts
- SQLite — collected Codex records, derived usage, and saved time markers
- JSON/JSONL — existing user metadata and Codex log input

The application runs locally on Windows and opens at `http://localhost:8501`.

Provide `setup.bat` for installation and `run.bat` for everyday use.

Bind only to localhost and disable telemetry.

## 10. MVP acceptance criteria

1. Automatically discover and parse local Codex sessions.
2. Calculate token consumption accurately, avoiding double-counting.
3. Detect available subagent relationships and agent roles.
4. Display an agent hierarchy and session usage breakdown.
5. Allow manual creation and labeling of runs.
6. Support runs covering complete sessions or selected time intervals.
7. Filter all statistics by labels and other dimensions.
8. Compare multiple groups of runs.
9. Save labels, annotations, and comparisons locally.
10. Support data refresh and CSV export.
11. Preserve original Codex files without modification.
12. Work fully offline without Codex authentication.
13. Clearly distinguish automatically observed facts, manual annotations, and estimated values.
14. Reimporting identical logs leaves collected records and usage totals unchanged. Rebuilding usage works from the collected records alone. A failed refresh or rebuild leaves the last successful usage dataset available.
15. Project and agent usage views show both the selected-period metrics and the metrics since a saved time marker within that period.

## 11. Implementation priorities

**Phase 1 — Reliable analytics**

Session parsing, token accounting, agent relationships, overview dashboard, and filtering.

**Phase 2 — Annotations and runs**

Manual labels, run boundaries, metadata persistence, and session-level breakdown.

**Phase 3 — Experiment comparison**

Group definitions, comparative charts, saved experiments, and distribution analysis.

The application should remain small, without plugin frameworks, distributed components, external databases, or background services.
