## Title

Align the application shell and Overview layout

## Goal

Give the app a shared header, persistent left navigation, and a main content area that switches between Overview and Manual annotations.

## Work

- Follow the [main layout](../specification/01-screens/000-main-layout.md), [header](../specification/01-screens/020-header.md), and [navigation](../specification/01-screens/010-navigation.md) specifications. Keep the existing title in `src/app.py` or render it once from the dashboard shell. Move the date range out of the sidebar into the shared header, default it to **All Time**, and preserve the selected range when switching views. Reuse the current date filtering and time-zone handling.
- In `src/internal/ui/dashboard.py`, limit the left navigation to **Overview** and **Manual annotations**. Open Overview by default and render the selected view in the main content region. Keep the shared shell available in empty and failed-import states.
- Follow the [content layout](../specification/01-screens/030-content.md#32-content-responsibilities). Put refresh, report filters, saved marker selection, dimension, grouping, and sorting in an Overview configuration block above the results. Move the existing controls from `dashboard.py` and `statistics_ui.py` as needed. Reuse the current KPI, chart, session detail, hierarchy, timeline, and CSV renderers. Apply sorting to the applicable Overview output.
- Separate the marker selector from the editor in `statistics_ui.py`. Render the existing editor in the Manual annotations body. Task 26 adds scope selection and its reporting behavior.
- Remove label and run controls, run-only results and exports, and the run-based experiment panel from the rendered views. Preserve existing saved files. Task 27 adds session comparisons as an Overview section. Keep the changes focused on screen composition and supported controls. The processing-speed formula and the source of execution-mode evidence after removing run and label controls remain separate specification questions.

## Acceptance Criteria

- On launch, the header shows the system title and **All Time**, the left navigation has exactly two entries, and Overview is selected.
- Switching views changes only the main content and preserves the date selection. Overview shows configuration before results. Manual annotations shows the existing editor.
- Overview charts, tables, and CSV retain the existing shared filtering and committed data behavior. Refresh failures show a diagnostic and keep the last usable results.
- The sidebar contains navigation only. Run and label controls and run-based comparisons are absent from both rendered views. Existing saved files are preserved.
