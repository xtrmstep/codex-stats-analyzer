# General layout

This document defines the minimal application shell for the simplified product scope. The current product definition includes only an overview page and a manual annotations page; no runs or labels are part of the system.

## 0.1 Page shell

The application is organized into three primary regions:

- `0.1` sidebar region
- `0.2` header region
- `0.3` main content region

```text
+--------------------------------------------------------------------------------------+
| [0.2] Header                                                                         |
|   - system title                                                                     |
+------------------------------+-------------------------------------------------------+
| [0.1] Sidebar                | [0.3] Main content                                    |
|   - Navigation               |   - refresh actions, KPIs, and charts                 |
|   - Overview configuration   |   - manual annotations editor                         |
|   - Filters (collapsible)    |                                                       |
+------------------------------+-------------------------------------------------------+
```

The page shell is a conceptual reference for the simplified UI. Detailed behavior for each region is defined in the related documents:

- Sidebar: [010-navigation.md](./010-navigation.md) (`1.x`)
- Header: [020-header.md](./020-header.md) (`2.x`)
- Content: [030-content.md](./030-content.md) (`3.x`)

## 0.2 Region responsibilities

### 0.2.1 Sidebar region

The left sidebar contains persistent **Navigation**. On Overview, it also contains **Overview configuration** and collapsible **Filters**. See the [sidebar specification](./010-navigation.md).

### 0.2.2 Header region

The header shows the system title. See [020-header.md](./020-header.md).

### 0.2.3 Main content region

The main content region contains the currently selected page body. This includes overview analytics and manual annotation configuration. It is described in [030-content.md](./030-content.md).

## 0.3 Unresolved details

The current scope does not confirm:

- exact menu labels or icons
- whether the left navigation is collapsible
- whether the header includes search, actions, or status indicators
- whether manual annotations uses a form, a modal, or a dedicated page layout

These remain open for later UI specification work.
