# Navigation

This document defines the minimal navigation structure implied by the functional specification for the dashboard and annotation workflows. It intentionally avoids inventing exact labels or styling beyond the supported conceptual sections.

## 1.1 Navigation sketch

```text
+---------------------------------------------------------------+
| [1.1] Navigation                                              |
|                                                               |
|  1.1.1 Overview / Dashboard                                   |
|  1.1.2 Sessions / Agent detail                               |
|  1.1.3 Runs / Metrics                                         |
|  1.1.4 Labels / Filtering                                     |
|  1.1.5 Manual annotations / Metadata                          |
|                                                               |
+---------------------------------------------------------------+
```

The sketch is a simplified model for the app shell shown in [00-general-layout.md](./00-general-layout.md) (`0.1`). It represents the functional areas that are explicitly supported by the existing specification.

## 1.2 Supported sections

### 1.2.1 Overview / dashboard

This section corresponds to the BI dashboard requirements in the primary specification, especially the global filters and overview KPIs. The dashboard is the default high-level entry point for aggregate analysis.

### 1.2.2 Sessions / agent detail

This section represents the direct analysis of sessions and their token/accounting details, including agent hierarchy and execution timeline views. The primary specification calls for session-level metrics, agent-role analysis, and timeline interpretation.

### 1.2.3 Runs / metrics

This section covers run-level usage and interval analysis, including created runs, annotations, and metric calculation for selected time ranges.

### 1.2.4 Labels / filtering

This section represents label management and filter-driven analysis. The specification explicitly requires creating, editing, deleting, assigning, and filtering labels across sessions and runs.

### 1.2.5 Manual annotations / metadata

This section represents run creation and metadata editing, including names, descriptions, labels, task identifiers, task type, outcome, scoring, and notes.

## 1.3 Navigation behavior

### 1.3.1 Selection behavior

Selecting a navigation item changes the page or panel shown in the main content region described in [03-content.md](./03-content.md) (`3.x`). The specification requires that dashboard visualizations respond to selected filters, but it does not define a separate navigation mode or routing model.

### 1.3.2 Hierarchy of views

The navigation model is intentionally shallow. The supported specification points to dashboard-level summaries and detail-level analyses, but does not define further nested menus or page trees.

## 1.4 Unresolved details

The specification does not confirm:

- exact menu naming or iconography
- whether sections are accordion-based or static
- whether a collapsible side rail is part of the UI
- whether the left navigation persists on all screens or only in dashboard context

These are intentionally left open for a later UI specification pass.
