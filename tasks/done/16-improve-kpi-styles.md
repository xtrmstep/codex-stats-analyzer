## Title

Improve KPI styling to display complete numeric values

## Goal

Ensure all KPI values in the Codex Usage Analyzer dashboard are fully visible without truncation. Preserve exact numeric values, existing metrics, and the overall dashboard structure.

## Work

Improve KPI typography and layout using Streamlit's native styling capabilities.

- Adjust KPI font size and weight to accommodate large numbers without unnecessary truncation.
- Enable a wider dashboard layout to provide more horizontal space.
- Keep the existing five-column KPI layout on desktop screens.
- Separate explanatory text, such as `(known only)`, from numeric KPI values.
- Preserve thousand separators, decimal precision, percentage symbols, and existing coverage information.
- Review the minimum supported Streamlit version and update it only if required by the selected styling options.
- Avoid custom CSS and additional UI components unless native styling cannot meet the requirements.

### Technical hints

Relevant files:

- `dashboard.py` — KPI rendering and value formatting, particularly lines 23–36 and 149–168.
- `app.py` — Streamlit page configuration.
- `.streamlit/config.toml` — Streamlit theme configuration.
- `requirements.txt` — Supported Streamlit versions.

Streamlit supports native KPI typography configuration. Suggested starting values:

```toml
[theme]
metricValueFontSize = "1.5rem"
metricValueFontWeight = 400
```

Consider enabling wide layout in `app.py`:

```python
st.set_page_config(
    page_title="Codex Usage Analyzer",
    layout="wide",
)
```

The current KPI implementation uses:

```python
columns = st.columns(5)
```

Preserve this layout where it provides sufficient space.

For run averages, the current implementation includes explanatory text inside the value:

```python
f"{run_mean:,.1f} (known only)"
```

Prefer keeping only the formatted numeric value in the KPI and moving the explanation into a caption or tooltip.

### Scope constraints

- Do not modify KPI calculations, filters, or data processing.
- Do not abbreviate numbers using K, M, or B.
- Do not introduce unrelated dashboard changes.
- Keep the implementation minimal and maintainable.

## Acceptance Criteria

- KPI values are displayed with complete numbers, including values such as `95,961,234` and `1,234,567,890`.
- Numeric values retain existing thousand separators and decimal precision.
- All five primary KPI metrics remain in one row at standard desktop widths when sufficient space is available.
- KPI typography uses a readable font size and weight.
- The dashboard uses the available horizontal space effectively.
- Explanatory text does not cause KPI values to truncate.
- Unknown values and partial-coverage indicators retain their existing meaning.
- Existing KPI calculations and data structures remain unchanged.
- Streamlit configuration options are compatible with the declared dependency version.
- The change can be checked through code review, configuration validation, and focused UI inspection without full end-to-end testing.
