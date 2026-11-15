## Title

Place the refresh buttons in one row above Overview configuration

## Specification

Follow the [Overview configuration layout](../specification/01-screens/030-content.md#321-view-parameters--view-configuration). Both refresh actions already exist from task 48.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), create a two-column Streamlit row in `_render()` immediately before `st.subheader("Overview configuration")`. Move **Incremental refresh** into the left column and **Full refresh from source** into the right column. Reuse their existing `incremental_requested` and `full_requested` values and preserve the full refresh help text.
- Keep **Date range** and **Time aggregation** under the heading in their current order. Limit changes to placement in the Overview. Preserve the importer routing, first-use behavior, diagnostics, and Manual annotations.

## Acceptance Criteria

- Overview renders both refresh buttons on one horizontal row directly above **Overview configuration**. The date range and time aggregation controls remain below the heading.
- Each button still triggers its existing refresh action. The full refresh help is still available and Manual annotations shows no refresh controls.
