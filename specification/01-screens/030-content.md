# Content area

This document defines the minimal content area for the two supported application views: overview and manual annotations. It intentionally defers detailed page layouts and individual widgets.

## 3.1 Content sketch

```text
+--------------------------------------------------------------------------+
| [3.1] View Parameters / View Configuration                                |
|   - source refresh                                                        |
|   - dimension selection                                                   |
|   - grouping selection                                                    |
|   - sorting selection                                                     |
+--------------------------------------------------------------------------+
| [3.2] Metrics                                                            |
|   - Overview KPIs                                                         |
|       - total input tokens                                                |
|       - total output tokens                                               |
|       - processing speed                                                  |
|       - other summary indicators                                          |
|   - Trends and charts                                                     |
|       - hourly and daily trend over time                                   |
|       - breakdown by selected view parameters                             |
+--------------------------------------------------------------------------+
```

This conceptual layout corresponds to the main content region in [000-main-layout.md](./000-main-layout.md) (`0.3`).

## 3.2 Content responsibilities

### 3.2.1 View Parameters / View Configuration

The first block is dedicated to defining how data is viewed. The user can configure:

- `3.2.1.3` dimension selection
- `3.2.1.4` grouping criteria, including time aggregation
- `3.2.1.5` sorting criteria

This block also contains **Refresh sources**. Overview results use the [header date range](./020-header.md#22-header-elements) and the [sidebar filters](./010-navigation.md#15-filters).

### 3.2.2 Metrics

The second block displays summary metrics and trend visualizations.

#### 3.2.2.1 Overview KPIs

Show total, input, and output tokens, input and output distribution, cache percentage, agent counts, processing speed, average daily tokens, and subagent token share where independently attributable. Distinguish observed facts, manual annotations, and estimates.

#### 3.2.2.2 Trends and charts

Show token trends by hour, day, week, or month. Include project and agent trends, agent usage by project, breakdowns by model, and cached versus non-cached input. Agent trends and agent usage by project group threads by recorded agent name, falling back to role; show Unknown when neither is available. The agent filter selects individual threads. Use nicknames to identify individual executions where available. Support filtering, grouping, sorting, and CSV export.

#### Saved time markers

Users can create, rename, edit, and delete named timestamps. Markers have no chat criterion, apply across chats, and persist across restarts and rebuilds.

#### Reporting windows

Filter by inclusive recorded calendar date, group using recorded clock labels (with weeks starting Monday), and display recorded timestamps and offsets. Compare marker instants using their offsets. When mixed offsets do not establish a single elapsed duration, leave the corresponding rate unknown.

Show **Full selected period** and, when a marker is selected, **Since [marker name]** together. The latter is the intersection of the selected range and the time starting at the marker, inclusive. Apply the same filters across chats to both; the marker adds only the inclusive cutoff. Show the marker timestamp and effective bounds, and display **No time in range** for an empty intersection. Place legacy deltas by observation time and flag uncertain attribution if a delta spans the cutoff. Use the [token accounting rules](../02-architecture/02-design/020-backend-class-design.md#token-accounting) for coverage and rates.

## 3.3 Content behavior

### 3.3.1 Parameter-driven updates

Metrics and charts update according to the header date range, sidebar filters, and applicable view configuration. If source refresh fails, show a diagnostic and keep displaying the last committed results.

### 3.3.2 Scope boundaries

This document intentionally does not define:

- exact field layout within the configuration block
- exact chart types where unspecified
- a separate manual-annotations management surface

The spec remains minimal until a later UI pass adds page-specific details.

## 3.4 Unresolved details

The current scope does not confirm:

- the exact values for grouping dimensions such as conversation, agent, or agent role
- whether ordering is ascending, descending, or user-defined
- whether the configuration block is collapsible or always visible

These are intentionally deferred.
