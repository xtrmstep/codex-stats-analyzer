"""Streamlit controls and tables for committed usage measurements."""

from datetime import datetime
from textwrap import wrap

import pandas as pd
import plotly.express as px
import streamlit as st

from internal.analytics.usage_statistics import StatsRequest, delete_marker, list_markers, save_marker


def marker_selector(writer):
    """Select an existing marker for the Overview report."""
    markers = list_markers(writer.connection)
    by_id = {marker.marker_id: marker for marker in markers}
    choice = st.selectbox("Saved time marker", ["None"] + list(by_id),
                          format_func=lambda key: by_id[key].name if key in by_id else key)
    return by_id.get(choice)


def marker_editor(writer):
    """Create, edit, or delete saved markers."""
    markers = list_markers(writer.connection)
    by_id = {marker.marker_id: marker for marker in markers}
    if "new_marker_default_timestamp" not in st.session_state:
        st.session_state["new_marker_default_timestamp"] = datetime.now().astimezone().isoformat()
    st.subheader("Saved time markers")
    choice = st.selectbox("Marker to edit", ["Create new marker"] + list(by_id),
                          format_func=lambda key: by_id[key].name if key in by_id else key)
    selected = by_id.get(choice)
    with st.form("marker_editor"):
        name = st.text_input("Name", value=selected.name if selected else "")
        timestamp = st.text_input("Timestamp with time zone",
                                  value=selected.timestamp if selected else st.session_state["new_marker_default_timestamp"])
        save = st.form_submit_button("Save marker")
    if save:
        try:
            save_marker(writer, name, timestamp, selected.marker_id if selected else None)
            st.rerun()
        except (ValueError, OverflowError) as exc:
            st.error(str(exc))
    if selected and st.button("Delete marker"):
        delete_marker(writer, selected.marker_id)
        st.rerun()


def _number(value, suffix=""):
    if value is None:
        return "Unknown"
    return (f"{value:,.1f}" if isinstance(value, float) else f"{value:,}") + suffix


def _row(measurement, view):
    return {
        "Project": measurement.project,
        "Agent": (measurement.agent or "Default") if view in {"Agent over time", "Agent by project over time", "By agent"} else None,
        "Model": measurement.agent if view in {"Model over time", "By model"} else None,
        "Time": measurement.bucket.isoformat() if measurement.bucket is not None else None,
        "Total tokens": measurement.totals["total_tokens"],
        "Coverage": measurement.coverage,
    }


def _name_key(name):
    """Order missing and present names consistently, ignoring case first."""
    name = name or ""
    return name.casefold(), name


def _measurement_key(measurement, view):
    """Return the prescribed ordering key for a breakdown measurement."""
    if view.endswith("over time"):
        names = (_name_key(measurement.project) + _name_key(measurement.agent or "Default")
                 if view == "Agent by project over time" else
                 _name_key(measurement.project if view == "Project over time" else measurement.agent))
        return (measurement.bucket is None, measurement.bucket or pd.Timestamp.max, *names)
    if view == "By project":
        return _name_key(measurement.project)
    return _name_key(measurement.agent)


def render_statistics(calculator, selection, marker, project_keys, selected_agents, bucket):
    """Calculate and render each scope's seven usage breakdowns."""
    request = StatsRequest(start_date=selection.start_date, end_date=selection.end_date,
                           bucket=bucket,
                           marker=marker, projects=project_keys, models=selection.models,
                           roles=selection.agent_roles,
                           agents=selected_agents)
    result = calculator.calculate(request)
    for scope_index, (scope, (summary, groups)) in enumerate(result.items()):
        if scope != "Full selected period":
            st.subheader(scope)
            if marker:
                st.caption(f"Marker: {marker.timestamp}")
        if summary.empty_window:
            st.info("No time in range")
            continue
        start_label = summary.start.isoformat() if summary.start is not None else "Unknown"
        end_label = summary.end.isoformat() if summary.end is not None else "Unknown"
        date_label = f"Recorded dates: {selection.start_date or 'unbounded'} to {selection.end_date or 'unbounded'} (inclusive). " if selection.start_date or selection.end_date else ""
        st.caption(f"{date_label}Effective instants: {start_label} to {end_label}. Coverage: {summary.coverage}.")
        kpis = [
            ("Total tokens", _number(summary.totals["total_tokens"]),
             "`sum(recorded total tokens)` = `Input tokens + Output tokens` when coverage is complete."),
            ("Input tokens", _number(summary.totals["input_tokens"]),
             "`sum(recorded input tokens)` = `Cached input + Non-cached input` when coverage is complete."),
            ("Output tokens", _number(summary.totals["output_tokens"]), "`sum(recorded output tokens)`"),
            ("Cached input", _number(summary.totals["cached_input_tokens"]), "`sum(recorded cached input tokens)`"),
            ("Non-cached input", _number(summary.totals["non_cached_input_tokens"]),
             "`sum(input tokens − cached input)` for records with both counts."),
            ("Cache percentage", _number(summary.cache_percentage, "%"),
             "`100 × sum(cached input) ÷ sum(input tokens)` for records with both counts."),
            ("Daily average", _number(summary.average_daily_tokens),
             "`Total tokens ÷ reporting window duration in days`"),
        ]
        table_key = f"overview_kpis_{scope_index}"
        with st.container(key=table_key):
            st.markdown(f"""
                <style>
                .st-key-{table_key} table {{ width: 100%; table-layout: fixed; font-size: 14px; }}
                .st-key-{table_key} th, .st-key-{table_key} td {{
                    padding: 0.2rem 0.4rem; white-space: normal; overflow-wrap: anywhere;
                }}
                .st-key-{table_key} th:nth-child(1) {{ width: 24%; }}
                .st-key-{table_key} th:nth-child(2) {{ width: 16%; }}
                .st-key-{table_key} th:nth-child(2), .st-key-{table_key} td:nth-child(2) {{ text-align: right; }}
                .st-key-{table_key} code {{
                    font-size: 14px; white-space: normal; overflow-wrap: anywhere;
                }}
                </style>
            """, unsafe_allow_html=True)
            st.markdown("| Name | Value | Description |\n| --- | --- | --- |\n" +
                        "\n".join(f"| {name} | {value} | {description} |" for name, value, description in kpis))
        st.caption(f"Agent threads: {summary.agents:,}")
        st.caption("Missing, conflicting, or incomplete response usage can make coverage partial.")
        sections = (
            ("Token consumption over time", (
                ("Project over time", "Project over time", "Project"),
                ("Agent over time", "Agent over time", "Agent"),
                ("Agent by project over time", "Agent by project over time", "Agent"),
                ("Model over time", "Model over time", "Model"))),
            ("Total token consumption", (
                ("By model", "Model", "Model"),
                ("By project", "By project", "Project"),
                ("By agent", "By agent", "Agent"))),
        )
        for section, charts in sections:
            st.subheader(section)
            for title, group_key, series in charts:
                st.markdown(f"##### {title}")
                ordered = sorted(groups[group_key], key=lambda item: _measurement_key(item, title))
                rows = [_row(item, title) for item in ordered]
                if not rows or not any(row["Total tokens"] is not None for row in rows):
                    st.info("No plottable usage for this chart.")
                    continue
                chart = pd.DataFrame(rows)
                chart[series] = chart[series].fillna("Unknown")
                trend = title.endswith("over time")
                x = "Time" if trend else series
                kwargs = {}
                if title == "Agent by project over time":
                    chart["Project"] = chart["Project"].fillna("Unknown")
                    kwargs["facet_col"] = "Project"
                    kwargs["facet_col_spacing"] = min(0.10, 0.5 / max(chart["Project"].nunique() - 1, 1))
                if trend and chart["Time"].isna().any():
                    chart["Time"] = chart["Time"].fillna("Unknown")
                    kwargs["category_orders"] = {"Time": list(dict.fromkeys(chart["Time"]))}
                elif trend:
                    chart["Time"] = pd.to_datetime(chart["Time"])
                figure = px.bar(chart, x=x, y="Total tokens", color=series, hover_data=["Coverage"], **kwargs)
                if trend and "category_orders" in kwargs:
                    figure.update_xaxes(type="category")
                top_margin = 20
                height = 300 if trend else 260
                if title == "Agent by project over time":
                    lines = [wrap(annotation.text, width=18, break_on_hyphens=False) or [""]
                             for annotation in figure.layout.annotations]
                    for annotation, parts in zip(figure.layout.annotations, lines):
                        annotation.text = "<br>".join(parts)
                    top_margin = max(40, 18 * max((len(parts) for parts in lines), default=1))
                    height = max(340, 280 + top_margin)
                elif not trend and chart[x].astype(str).str.len().max() > 24:
                    height = 310
                figure.update_layout(height=height, margin=dict(l=20, r=20, t=top_margin, b=35))
                figure.update_xaxes(automargin=True)
                figure.update_yaxes(automargin=True)
                if title == "Agent by project over time":
                    figure.update_xaxes(nticks=2, tickangle=0)
                    if "category_orders" not in kwargs:
                        tick_format = "%b %d\n%H:%M" if bucket == "hourly" else "%b %Y" if bucket == "monthly" else "%b %d"
                        figure.update_xaxes(tickformat=tick_format)
                st.plotly_chart(figure, use_container_width=True, key=f"usage_{scope_index}_{group_key}")
