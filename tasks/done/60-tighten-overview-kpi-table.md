## Title

Tighten the Overview KPI table layout

## Specification

Follow the [Overview KPI table](../specification/01-screens/030-content.md#3221-overview-kpis). This task is independent of chart sizing.

## Work

- In [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), tighten the header and cell padding of the existing KPI table. Right-align the **Value** column. Allow the **Description** text and inline formulas to wrap so the table can fit narrower content widths. Keep a readable font size and all three columns.
- Keep styling scoped to the KPI table in both reporting windows, such as by placing the existing Markdown table in a keyed Streamlit container with table-specific CSS. Reuse the existing row values, formula strings, and `_number()` formatting. Keep the current chart layout, report captions, empty-window behavior, and application-wide styles.

## Acceptance Criteria

- At the same desktop width the table uses less vertical space than the current Markdown table. It keeps seven rows in the same order, right-aligned values, and visible formulas. Zero, percentages, and **Unknown** retain their existing display.
- At a narrower width with the sidebar open, longer formulas wrap and remain readable. With a marker selected, both tables use the same styling. Other tables and Manual annotations are unaffected.
