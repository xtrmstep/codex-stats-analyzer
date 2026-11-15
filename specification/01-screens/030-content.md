# Content area

This document defines the minimal content area for the two supported application views: overview and manual annotations. It intentionally defers detailed page layouts and individual widgets.

## 3.1 Content sketch

```text
+--------------------------------------------------------------------------+
|   [Incremental refresh]  [Full refresh from source]                       |
+--------------------------------------------------------------------------+
| [3.2] Metrics                                                            |
|   - KPI table                                                             |
|   - Token consumption over time                                           |
|   - Total token consumption                                               |
+--------------------------------------------------------------------------+
```

This conceptual layout corresponds to the main content region in [000-main-layout.md](./000-main-layout.md) (`0.3`).

## 3.2 Content responsibilities

### 3.2.1 Refresh actions

Show **Incremental refresh** and **Full refresh from source** side by side in a single row at the top of the Overview main content. Results use the [sidebar configuration](./010-navigation.md#16-overview-configuration) and [filters](./010-navigation.md#15-filters).

**Incremental refresh** loads new records and retains imported history. **Full refresh from source** replaces the imported dataset with the source records currently available. Explain beside the full refresh action that previously imported history can disappear and that saved markers and agent names are kept. See [source collection](../02-architecture/02-design/000-system-overview.md#component-behavior).

### 3.2.2 Metrics

The second block displays summary metrics and trend visualizations.

#### 3.2.2.1 Overview KPIs

Show a compact, read-only KPI table above the charts. The standard columns are **Name**, **Value**, and **Description**, in that order. Use tight cell spacing, right-align values, and let formula descriptions wrap on narrow screens. Display the formulas below in the listed row order, using **Unknown** for unavailable values. Show the agent count and coverage alongside the table. Distinguish observed facts, manual annotations, and estimates. Use the [token accounting and rate rules](../02-architecture/02-design/020-backend-class-design.md#token-accounting).

When comparison is enabled, add a right-aligned **Previous period** value column between **Value** and **Description** in the selected-period table. Keep one row per KPI and use **Unknown** for unavailable comparison values.

| Name | Description |
| --- | --- |
| Total tokens | `Input tokens + Output tokens` |
| Input tokens | `Cached input + Non-cached input` |
| Output tokens | `sum(response output tokens)` |
| Cached input | `sum(response cached input)` |
| Non-cached input | `Input tokens − Cached input` |
| Cache percentage | `100 × Cached input ÷ Input tokens` |
| Daily average | `Total tokens ÷ Elapsed days` |

The formulas summarize the relationships between KPIs. Values use recorded counters and paired counts according to the token accounting rules. The coverage caption indicates incomplete data.

#### 3.2.2.2 Trends and charts

Below the KPIs, show the seven chart views in these two sections, in order.

Show the charts in a single column with compact heights, margins, and title spacing. Give charts more room when needed for readable axis labels, legends, or project facet labels.

When comparison is enabled, show the Overview charts in two columns headed **Selected period** and **Previous period**, with the inclusive dates under each heading. Pair corresponding charts on the same row. Keep the empty state in its chart cell when that period has no plottable usage.

| Section | Chart | Grouping |
| --- | --- | --- |
| Token consumption over time | Project over time | Project and time bucket |
| | Agent over time | Agent and time bucket |
| | Agent by project over time | Project, agent, and time bucket, with agents grouped visibly by project |
| | Model over time | Model and time bucket |
| Total token consumption | By model | Model across the window |
| | By project | Project across the window |
| | By agent | Agent across the window |

All seven charts use the same filtered usage and display total tokens. The trend charts use the selected time aggregation and show buckets from oldest to newest by recorded clock time. An unknown bucket appears after dated buckets when present. The three summaries aggregate the entire reporting window and keep the same totals when time aggregation changes. Show a readable unknown attribution label where applicable and distinguish unknown token counts from zero.

Group agent charts by reporting name. Use the user-assigned name if present, otherwise the recorded name, then the recorded role, then **Default**. The [sidebar Agent filter](./010-navigation.md#15-filters) uses the same reporting name.

Use an empty state for a chart without plottable totals and retain the reporting window's empty-range state. Within each trend breakdown, order data by time bucket and then group name. Order summary categories by group name.

#### Saved time markers

Manage saved time markers on the [Manual Annotations page](#34-manual-annotations). Markers apply across chats and persist across restarts and rebuilds.

#### Reporting windows

Filter by inclusive recorded calendar date, group using recorded clock labels (with weeks starting Monday), and display recorded timestamps and offsets. Compare marker instants using their offsets. When mixed offsets do not establish a single elapsed duration, leave the corresponding rate unknown.

Show the report for the selected period first, starting with its date and coverage caption. With [Compare to previous period](./010-navigation.md#compare-to-previous-period) enabled, compare it with the immediately preceding span of the same number of inclusive calendar days. The comparison ends one day before the selected period begins. For example, October 12–18 compares with October 5–11. Use the same active filters and time aggregation in both periods.

When a marker is selected, show a separate **Since [marker name]** report below the Overview blocks, with its own three-column KPI table and single-column charts. Its window is the intersection of the selected range and the time starting at the marker, inclusive. Apply the same active filters and time aggregation. Show the marker timestamp and effective bounds, and display **No time in range** for an empty intersection. Use the [token accounting rules](../02-architecture/02-design/020-backend-class-design.md#token-accounting) for coverage and rates.

## 3.3 Content behavior

### 3.3.1 Parameter-driven updates

Metrics and charts update according to the Overview date range, sidebar filters, and applicable view configuration. If source refresh fails, show a diagnostic and keep displaying the last committed results.

### 3.3.2 Scope boundaries

This document intentionally does not define:

- exact chart types where unspecified

The spec remains minimal until a later UI pass adds page-specific details.

## 3.4 Manual Annotations

Show **Manual Annotations** as the page heading, with **Add new** above a table with **Name**, **Timestamp**, **Description**, and **Actions** columns. List all saved markers from oldest to newest. Display each timestamp in the app's local time as `YYYY-MM-DD HH:MM:SS`. Show **No saved time markers** when the list is empty. Each row has **Edit** and **Delete** buttons. **Delete** removes that row's marker and refreshes the table.

Start with the form hidden. **Add new** opens a form below the table with a blank name and description and the current local date and time. **Edit** opens the same form with the selected marker's saved values. **Description** is optional free text. Use **Date** and **Time** pickers and indicate the app's local time zone in the form. **Save** refreshes the table and closes the form on success. Keep the form open with the entered values and a message if validation fails.

Preserve the saved instant when only the name or description changes. Save changed times with the offset for the selected date and time. For a skipped or repeated local time, ask for a time that identifies one instant.
