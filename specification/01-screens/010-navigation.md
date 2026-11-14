# Sidebar

The sidebar provides navigation between Overview and Manual annotations and contains the filters for Overview.

## 1.1 Sidebar sketch

```text
+---------------------------------------------------------------+
| Navigation                                                     |
|                                                               |
|  1.1.1 Overview                                              |
|  1.1.2 Manual annotations                                    |
|                                                               |
| Filters (Overview)                                            |
|                                                               |
+---------------------------------------------------------------+
```

The sketch is a simplified model for the app shell shown in [000-main-layout.md](./000-main-layout.md) (`0.1`). It represents the full current scope of the application.

## 1.2 Supported sections

### 1.2.1 Overview

This section presents the aggregated statistics for the selected time range and filters. It is the default landing view for high-level analysis.

### 1.2.2 Manual annotations

This section allows users to create manual events and configure how those events contribute to aggregate stats. The user can define whether an event should include all stats or only selected chats, along with other event-level configuration.

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

Show **Filters** below **Navigation** when Overview is selected. It contains project, model, observed agent role, individual agent, execution mode, and saved time marker selection. The shared [date range](./020-header.md#22-header-elements) is in the header. Manual annotations uses its own editor controls in the main content area.

The filters determine which records contribute to Overview results. The saved time marker adds the [second reporting window](./030-content.md#reporting-windows).
