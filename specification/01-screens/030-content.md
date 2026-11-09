# Content area

This document defines the minimal content area for the two supported application views: overview and manual annotations. It intentionally defers detailed page layouts and individual widgets.

## 3.1 Content sketch

```text
+--------------------------------------------------------------------------+
| [3.1] View Parameters / View Configuration                                |
|   - additional filters                                                    |
|   - manual annotations / events filters                                   |
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

- `3.2.1.1` additional filters
- `3.2.1.2` filtering by manual annotations or events
- `3.2.1.3` dimension selection
- `3.2.1.4` grouping criteria
- `3.2.1.5` sorting criteria

These parameters determine the data slice being analyzed and should affect all metrics and chart output.

Manual annotations are treated as regular filtering parameters rather than a separate feature area. They extend the available filtering options for the current view.

### 3.2.2 Metrics

The second block displays summary metrics and trend visualizations.

#### 3.2.2.1 Overview KPIs

This section summarizes key indicators, including:

- total input tokens
- total output tokens
- processing speed
- additional relevant summary metrics

#### 3.2.2.2 Trends and charts

This section shows how metrics change over time, such as:

- hourly and daily trends
- grouped breakdowns based on the selected view parameters
- chart output reflecting the chosen dimensions, grouping, and filters

## 3.3 Content behavior

### 3.3.1 Parameter-driven updates

All metrics and charts update according to the selected view configuration. The current filtering choices, grouping, sorting, and manual-annotation filters should refresh the displayed KPI values and trend breakdowns.

### 3.3.2 Scope boundaries

This document intentionally does not define:

- exact field layout within the configuration block
- exact chart types beyond the trend and breakdown requirement
- individual metric formulas beyond summary examples
- a separate manual-annotations management surface

The spec remains minimal until a later UI pass adds page-specific details.

## 3.4 Unresolved details

The current scope does not confirm:

- the exact values for grouping dimensions such as conversation, agent, or agent role
- whether ordering is ascending, descending, or user-defined
- how manual annotation filters are expressed in the UI
- whether the configuration block is collapsible or always visible

These are intentionally deferred.
