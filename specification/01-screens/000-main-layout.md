# General layout

This document defines the minimal application shell for the simplified product scope. The current product definition includes only an overview page and a manual annotations page; no runs or labels are part of the system.

## 0.1 Page shell

The application is organized into three primary regions:

- `0.1` navigation region
- `0.2` header region
- `0.3` main content region

```text
+----------------------------------------------------------------------------------+
| [0.2] Header / page context / global filter controls                              |
|   - page title and current context                                                |
|   - global filters (date, project, model, session, agent role, execution mode)    |
+-------------------------+----------------------------------------------------------+
| [0.1] Navigation        | [0.3] Main content                                       |
|   - Overview             |   - overview KPIs and charts                              |
|   - Manual annotations   |   - manual event editor                                   |
+-------------------------+----------------------------------------------------------+
```

The page shell is a conceptual reference for the simplified UI. Detailed behavior for each region is defined in the related documents:

- Navigation: [01-navigation.md](./01-navigation.md) (`1.x`)
- Header: [02-header.md](./02-header.md) (`2.x`)
- Content: [03-content.md](./03-content.md) (`3.x`)

## 0.2 Region responsibilities

### 0.2.1 Navigation region

The navigation region is the persistent side area for the two supported views: overview and manual annotations. This is documented in [01-navigation.md](./01-navigation.md).

### 0.2.2 Header region

The header region contains the active page context and the supported global filters. It is described in [02-header.md](./02-header.md). No additional header controls are assumed unless they are explicitly added later.

### 0.2.3 Main content region

The main content region contains the currently selected page body. This includes overview analytics and manual annotation configuration. It is described in [03-content.md](./03-content.md).

## 0.3 Unresolved details

The current scope does not confirm:

- exact menu labels or icons
- whether the left navigation is collapsible
- whether the header includes search, actions, or status indicators
- whether manual annotations uses a form, a modal, or a dedicated page layout

These remain open for later UI specification work.
