## Title

Simplify the formulas in the KPI descriptions

## Specification

Use the [Overview KPI descriptions](../specification/01-screens/030-content.md#3221-overview-kpis). This is a standalone UI text change.

## Work

- In the `kpis` list in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), replace the seven Description strings with the compact formulas in the specification. In particular, **Total tokens** displays only `Input tokens + Output tokens`.
- Keep the **Name**, **Value**, and **Description** columns, row order, formula styling, and compact table layout. Keep each value sourced from the existing summary fields via `_number()`. The formula text summarizes the calculation and the current coverage caption continues to describe incomplete data.

## Acceptance Criteria

- The primary and **Since [marker]** tables show the same seven compact descriptions in the existing order. The Total tokens description contains just the addition formula.
- The same filtered report displays the same KPI values and coverage before and after, including when input or cache data is partial. Percentage formatting and **Unknown** remain intact.
