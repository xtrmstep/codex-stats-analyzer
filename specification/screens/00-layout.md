# General layout

This document defines the minimal application shell implied by the existing specification. It is intentionally conceptual: the final styling, spacing, and widget-level layout are deferred.

## 0.1 Page shell

The application is organized into three primary regions:

- `0.1` navigation region
- `0.2` header region
- `0.3` main content region

```text
+----------------------------------------------------------------------------------+
| [0.2] Header / page context / global filter controls                              |
|   - page title and current context                                                |
|   - global filters (date, project, model, session, agent role, labels,            |
|     task type, execution mode)                                                   |
+-------------------------+----------------------------------------------------------+
| [0.1] Navigation        | [0.3] Main content                                       |
|   - dashboard overview  |   - KPI summary                                            |
|   - session detail      |   - visualizations                                        |
|   - runs / labels       |   - detail tables                                         |
|   - manual annotations  |                                                          |
+-------------------------+----------------------------------------------------------+
```

The page shell is a reference model for the application described in the primary specification. Detailed behavior for each region is defined in the related documents:

- Navigation: [01-navigation.md](./01-navigation.md) (`1.x`)
- Header: [02-header.md](./02-header.md) (`2.x`)
- Content: [03-content.md](./03-content.md) (`3.x`)

## 0.2 Region responsibilities

### 0.2.1 Navigation region

The navigation region is the persistent side area that gives access to the main views implied by the existing specification. The navigation requirements are documented in [01-navigation.md](./01-navigation.md) and intentionally remain high-level because the specification defines supported functionality rather than exact labels.

### 0.2.2 Header region

The header region is the top-of-page control area for page context and global filtering. It is described in [02-header.md](./02-header.md). The specification explicitly names the supported filters; no additional header actions are assumed.

### 0.2.3 Main content region

The main content region contains the active page body and is where the dashboard, tables, and detail information are displayed. It is described in [03-content.md](./03-content.md).

## 0.3 Unresolved details

The specification does not confirm:

- exact menu labels or icons
- whether the left navigation is collapsible
- whether the header includes search, notifications, or other utility controls
- exact widget placement within the main content page

These details remain open for later UI specification work.
