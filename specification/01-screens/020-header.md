# Header

This document describes the minimal header region for the application shell shown in [000-main-layout.md](./000-main-layout.md) (`0.2`). The product scope currently includes overview analytics and manual annotations, without any run or label system.

## 2.1 Header sketch

```text
+---------------------------------------------------------------+
| [2.1] System title                                            |
| [2.2] Date range: All Time                                    |
+---------------------------------------------------------------+
```

This is a conceptual header and does not imply any specific visual style or component library.

## 2.2 Header elements

### 2.2.1 System title

The header displays the system title only. It does not display page context or additional actions in the current simplified scope.

### 2.2.2 Date range

The header displays the date range selector, which defaults to `All Time` and is already understood to work correctly. No additional date-range specification is required here.

## 2.3 Header behavior

### 2.3.1 Minimal state

The header remains minimal and stable. There are no filter controls beyond the date range, and no page-specific context is shown in the header.

## 2.4 Unresolved details

The current scope does not confirm:

- whether the system title is rendered as text or a logo
- whether the date range control is presented as a dropdown, button, or compact selector
- whether future versions may add additional header controls

These remain open for later UI specification work.
