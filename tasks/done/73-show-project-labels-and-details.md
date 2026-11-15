## Title

Show short project labels and full identifiers in the sidebar

## Specification

Follow the [Projects filter and Project details](../specification/01-screens/010-navigation.md#project-labels). Use the label helper from task 72.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), build the mapping once from the published snapshot before applying date ranges or filters. Keep the real project keys as the `st.multiselect()` options and use the label mapping for display and sorting by label. Keep the existing key-to-source-directory mapping for downstream filtering.
- Place a collapsed **Project details** section immediately below **Projects** within **Filters**. List each known project once in a read-only **Short label** and **Full project identifier** table. Use the same labels and ordering as the filter. If no known projects exist, keep the Projects filter empty and show an empty state in the details section.

## Acceptance Criteria

- Filter options and selected values show compact labels. Selecting either of two projects that share a base label returns the same results as selecting its original key.
- **Project details** resolves each label to a full repository identifier or working path. It lists all known projects regardless of the selected date range or comparison mode. Verify that a long value can be read in full from the table in the sidebar. Opening the section leaves the filters and calculations unchanged.
