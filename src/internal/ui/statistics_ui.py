"""Streamlit controls and tables for committed usage measurements."""

from datetime import datetime

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
        st.subheader(scope)
        if marker and scope != "Full selected period":
            st.caption(f"Marker: {marker.timestamp}")
        if summary.empty_window:
            st.info("No time in range")
            continue
        start_label = summary.start.isoformat() if summary.start is not None else "Unknown"
        end_label = summary.end.isoformat() if summary.end is not None else "Unknown"
        date_label = f"Recorded dates: {selection.start_date or 'unbounded'} to {selection.end_date or 'unbounded'} (inclusive). " if selection.start_date or selection.end_date else ""
        st.caption(f"{date_label}Effective instants: {start_label} to {end_label}. Coverage: {summary.coverage}.")
        columns = st.columns(5)
        columns[0].metric("Total tokens", _number(summary.totals["total_tokens"]),
                          help="Sum of recorded total tokens for input and output.")
        columns[1].metric("Input tokens", _number(summary.totals["input_tokens"]),
                          help="Tokens sent to the model, including cached input.")
        columns[2].metric("Output tokens", _number(summary.totals["output_tokens"]),
                          help="Tokens generated by the model, including reasoning tokens when reported as output.")
        columns[3].metric("Cache percentage", _number(summary.cache_percentage, "%"),
                          help="Share of input served from cache where both input counts are known.")
        columns[4].metric("Daily average", _number(summary.average_daily_tokens),
                          help="Total tokens divided by the reporting window's duration in days.")
        extra_columns = st.columns(2)
        extra_columns[0].metric("Cached input", _number(summary.totals["cached_input_tokens"]),
                                help="Input tokens reused from cache.")
        extra_columns[1].metric("Non-cached input", _number(summary.totals["non_cached_input_tokens"]),
                                help="Input minus cached input where both counts are known.")
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
                st.markdown(f"#### {title}")
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
                if trend and chart["Time"].isna().any():
                    chart["Time"] = chart["Time"].fillna("Unknown")
                    kwargs["category_orders"] = {"Time": list(dict.fromkeys(chart["Time"]))}
                elif trend:
                    chart["Time"] = pd.to_datetime(chart["Time"])
                figure = px.bar(chart, x=x, y="Total tokens", color=series, hover_data=["Coverage"], **kwargs)
                if trend and "category_orders" in kwargs:
                    figure.update_xaxes(type="category")
                st.plotly_chart(figure, use_container_width=True, key=f"usage_{scope_index}_{group_key}")
