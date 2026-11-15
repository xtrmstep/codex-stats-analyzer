# Sidebar

The sidebar provides navigation between Overview and Manual annotations and contains Overview configuration and filters.

## 1.1 Sidebar sketch

```text
+---------------------------------------------------------------+
| Navigation                                                     |
|                                                               |
|  1.1.1 Overview                                              |
|  1.1.2 Manual annotations                                    |
|                                                               |
| Overview configuration                                       |
|   Date range, Time aggregation, Compare to previous period    |
| Filters (collapsible)                                         |
|                                                               |
+---------------------------------------------------------------+
```

The sketch is a simplified model for the app shell shown in [000-main-layout.md](./000-main-layout.md) (`0.1`). It represents the full current scope of the application.

## 1.2 Supported sections

### 1.2.1 Overview

This section presents the aggregated statistics for the selected time range and filters. It is the default landing view for high-level analysis.

### 1.2.2 Manual annotations

This section allows users to create, edit, and delete named time markers and to set or clear a user-assigned name for each agent execution. Markers have a timestamp and apply across chats. Identify executions using chat titles and available roles or nicknames; distinguish duplicate labels without displaying IDs.

## 1.3 Navigation behavior

### 1.3.1 Selection behavior

Selecting a navigation item changes the primary content area described in [030-content.md](./030-content.md) (`3.x`). The application does not define any additional nested navigation hierarchy beyond these two views.

### 1.3.2 Minimal page model

The current product scope is intentionally shallow. There are no run pages, no labels system, and no dashboard sub-navigation beyond the two supported top-level views.

## 1.4 Unresolved details

The current scope does not confirm:

- exact menu naming or iconography
- whether the navigation is static or collapsible
- whether the manual annotations mode is displayed as a dedicated page or a modal form

These remain open for later UI specification work.

## 1.5 Filters

On Overview, show one collapsible **Filters** section below [Overview configuration](#16-overview-configuration). Start it expanded. Collapsing it hides the controls and keeps their selections active. It contains project, model, observed agent role, chat, agent name, execution mode, and saved time marker selection. Manual annotations uses its own editor controls in the main content area.

- **Chat** lists distinct known titles available for the selected dates and other applicable filters. It defaults to **All chats** and returns to that value if the selected title becomes unavailable. A selected title includes the main agent and all subagents that have inherited that title from their verified root. If several chats share the same title, the option includes all of them. Usage from untitled chats remains available under **All chats**.
- **Agent** lists distinct agent and subagent names and defaults to **All agents**. Use the [reporting name](./030-content.md#3222-trends-and-charts) for each execution. With **All chats**, a selected name matches executions across chats. A selected chat title narrows the available agent names and the results. Keep a selected agent name while it remains available and reset to **All agents** when it becomes unavailable. **Agent roles** filters by observed role and combines with both selections.

The filters determine which records contribute to Overview results. The saved time marker adds the [since-marker report](./030-content.md#reporting-windows).

## 1.6 Overview configuration

On Overview, show **Overview configuration** below **Navigation** and above **Filters**. It contains **Date range**, **Time aggregation**, and **Compare to previous period**, in that order. Time aggregation offers hourly, daily, weekly, and monthly buckets.

### Date range

Resolve the presets against the app's local date each time Overview renders. In the option list and the selected value, show each bounded preset's name followed by its inclusive dates in `YYYY-MM-DD` format. **Today** shows one date, and **All Time** shows its name alone. The selected-period report uses the bounds shown in the selector.

| Preset | Date limits |
| --- | --- |
| **Today** | Today's date |
| **Last 7 days** (default) | Six calendar days before today through today |
| **Last 30 days** | Twenty-nine calendar days before today through today |
| **All Time** | Unbounded |
| **Current week** | This week's Monday through today |
| **Last week** | Last week's Monday through Sunday |
| **Current month** | This month's first day through today |
| **Last month** | Last month's first through last day |

### Compare to previous period

Show an unchecked checkbox by default. Disable it for **All Time**. Enabling it displays the [previous-period comparison](./030-content.md#reporting-windows) in the Overview KPI table and charts.
