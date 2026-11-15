## Title

Make the Overview filter section collapsible

## Specification

Follow the [sidebar Filters behavior](../specification/01-screens/010-navigation.md#15-filters).

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), replace the sidebar Filters container and its separate heading with one expander labeled **Filters**, initially expanded. Put both existing filter blocks inside the same expander, including the saved marker selector and the project, model, role, Chat, and Agent controls. Keep rendering the controls on every Overview run so their values continue to drive the report while the expander is closed.
- Preserve widget keys, filter defaults, the existing Chat and Agent options and reset rules, and filter application to both report windows. Keep Navigation and Overview configuration outside the expander.

## Acceptance Criteria

- On first open, the filter section is expanded. Select a project, a Chat and Agent where available, and a saved marker. Collapse the section and confirm the report still reflects those selections. Reopen it and confirm the same selections are visible.
- Change Date range while Filters is collapsed, then reopen it. Chat and Agent options still reflect the new dates and existing eligibility rules. Manual annotations has no Overview filter section.
