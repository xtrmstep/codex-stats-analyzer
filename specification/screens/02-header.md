# Header

This document describes the minimal header region for the application shell shown in [00-general-layout.md](./00-general-layout.md) (`0.2`). It is limited to elements explicitly supported by the existing specification.

## 2.1 Header sketch

```text
+----------------------------------------------------------------------------------+
| [2.1] Page title / current context                                              |
|                                                                                  |
| [2.2] Global filters                                                            |
|   - date range                                                                   |
|   - project                                                                      |
|   - model                                                                        |
|   - session                                                                      |
|   - agent role                                                                   |
|   - labels                                                                       |
|   - task type                                                                    |
|   - execution mode                                                               |
+----------------------------------------------------------------------------------+
```

This is a conceptual header and does not imply any specific visual style or component library.

## 2.2 Header elements

### 2.2.1 Page title and context

The header indicates the current page or analytic context. The specification names its purpose only indirectly by referring to dashboard views and annotations; it does not define an explicit title taxonomy for every page.

### 2.2.2 Global filters

The primary specification defines the supported global filters in section `6.1`:

- `2.2.2.1` date range
- `2.2.2.2` project
- `2.2.2.3` model
- `2.2.2.4` session
- `2.2.2.5` agent role
- `2.2.2.6` labels
- `2.2.2.7` task type
- `2.2.2.8` execution mode

These filters are global in the sense that all dashboard visualizations respond to them.

## 2.3 Header behavior

### 2.3.1 Filter-driven updates

Changing a filter updates the dashboard and associated content in the main area. This behavior is explicitly required by the specification: all dashboard visualizations respond to selected filters.

### 2.3.2 Context preservation

The header should preserve the active analytic context while the user changes filters or navigates between related views. The specification does not define a separate breadcrumb or persistent state mechanism.

## 2.4 Unresolved details

The specification does not confirm:

- whether filters are presented as dropdowns, chips, or a form
- whether the header includes search, actions, or status indicators
- whether the page title is always shown or only on certain views

These elements remain unresolved and should be specified later.
