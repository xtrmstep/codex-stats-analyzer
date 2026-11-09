# Content area

This document defines the minimal content-area structure implied by the BI dashboard and annotation workflows in the primary specification. It intentionally defers page-specific layouts and individual widgets.

## 3.1 Content sketch

```text
+--------------------------------------------------------------------------+
| [3.1] Overview / KPI summary                                            |
|   - total tokens                                                        |
|   - input/output distribution                                           |
|   - cache percentage                                                    |
|   - sessions / runs / agents                                             |
|   - average and median tokens per run                                    |
|   - subagent token share                                                |
+--------------------------------------------------------------------------+
| [3.2] Visualizations                                                    |
|   - token usage over time                                               |
|   - token consumption by project/model/session/run/label                 |
|   - cached vs. non-cached input distribution                            |
|   - main-agent vs. subagent token consumption                           |
|   - agent hierarchy and execution timeline                               |
+--------------------------------------------------------------------------+
| [3.3] Detail table                                                      |
|   - detailed sessions and runs                                          |
|   - filtered records                                                    |
+--------------------------------------------------------------------------+
```

This conceptual layout corresponds to the main content region in [00-general-layout.md](./00-general-layout.md) (`0.3`).

## 3.2 Content responsibilities

### 3.2.1 KPI summary

The top of the content area is reserved for overview KPIs. The primary specification enumerates the supported metrics in section `6.2`:

- `3.2.1.1` total tokens
- `3.2.1.2` input/output token distribution
- `3.2.1.3` cache percentage
- `3.2.1.4` sessions
- `3.2.1.5` runs
- `3.2.1.6` agents
- `3.2.1.7` average and median tokens per run
- `3.2.1.8` subagent token share

### 3.2.2 Visualizations

The visualization area contains the dashboard charts and analysis views enumerated in section `6.3`:

- `3.2.2.1` token usage over time with daily/weekly/monthly aggregation
- `3.2.2.2` token consumption by project, model, session, run, or label
- `3.2.2.3` cached versus non-cached input distribution
- `3.2.2.4` main-agent versus subagent token consumption
- `3.2.2.5` agent hierarchy and execution timeline
- `3.2.2.6` detailed sessions and runs table

### 3.2.3 Detail table

The lower content area is reserved for records and drill-down results. The primary specification requires a table for detailed sessions and runs and implies that selected filters should narrow the table content.

## 3.3 Content behavior

### 3.3.1 Filter reactivity

All dashboard visualizations respond to the selected filters from the header. This requirement is stated explicitly in the primary specification and should apply across KPI cards, chart sections, and the detail table.

### 3.3.2 Scope of page layouts

This document intentionally does not define the layout for individual pages or dashboard widgets. The current specification does not provide enough detail to fix those designs without inventing unsupported behavior.

## 3.4 Unresolved details

The specification does not confirm:

- exact widget arrangement within the content pane
- whether the KPI summary is a row of cards, a grid, or a single stacked block
- whether each visualization is an individual panel or a single combined dashboard
- whether annotation workflows have dedicated page layouts separate from the dashboard

These should be specified later as page-by-page UI designs.
