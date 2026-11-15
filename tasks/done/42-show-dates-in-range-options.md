## Title

Show resolved dates in the Date range selector

## Specification

Follow the [Overview Date range specification](../specification/01-screens/030-content.md#date-range). The preset calculation from completed task 39 is already available.

## Work

- In [`dashboard.py`](../src/internal/ui/dashboard.py), keep the existing preset names, option order, and **Today** default in `_render()`. Capture `date.today()` once per Overview render and resolve each option with `_date_limits(preset, today)`. Keep the resulting bounds in a local mapping and read `start, end` for the selected preset from that same mapping before constructing `Filters`.
- Use the existing `st.selectbox()` with `format_func` to show the formatted date labels while returning the original preset name. Keep the widget identity stable across rerenders. Use `Today (2026-11-15)` for the single-day preset, `Last week (2026-11-02 to 2026-11-08)` for a range, and `All Time` for unbounded dates. These dates are examples for a local date of 2026-11-15. Generate actual labels on every Overview render. [Streamlit selectbox reference](https://docs.streamlit.io/1.55.0/develop/api-reference/widgets/st.selectbox)
- Limit application changes to `dashboard.py`. Reuse the existing date arithmetic and filtering path. Preserve reporting-window captions, other filters, time aggregation, saved-marker behavior, and Manual annotations. The selector itself displays the dates, with no companion input, application-managed date state, or background refresh.

## Acceptance Criteria

- Opening the selector shows the existing six options in order. Every bounded option shows the inclusive dates for the app's local date, **Today** shows one date and is selected by default, and **All Time** appears without dates.
- Changing presets immediately shows the chosen label in the closed selector. Its displayed dates match the bounds sent to `Filters`; **All Time** still sends `(None, None)`.
- Rendering Overview for a different local day refreshes the labels and the report bounds for the active preset. Verify a rollover with a non-default preset selected and confirm that its name remains selected. Changing the saved marker leaves the Date range label unchanged.
