## Title

Add previous-period values to the KPI table

## Specification

Follow the [Overview KPI table specification](../specification/01-screens/030-content.md#3221-overview-kpis). Use the comparison summary from task 63.

## Work

- In the KPI table in [`statistics_ui.py`](../src/internal/ui/statistics_ui.py), show **Name**, **Value**, **Previous period**, and **Description** when a comparison summary is supplied for the selected-period table. Read both periods from the same KPI field mapping and format both using `_number()`.
- Adjust the table's scoped column widths and alignment for the extra numeric column. Keep the compact styles, existing descriptions, and wrapping. Keep the three-column layout when there is no comparison and for the **Since [marker name]** table.

## Acceptance Criteria

- Each of the seven KPI rows shows the correct selected and previous values in the same row. Percentages retain their formatting, zero remains visible, and missing comparison values show **Unknown**.
- Both numeric columns are right-aligned and the descriptions wrap. The selected-period values, row order, and descriptions stay the same. The marker report keeps its three columns.
