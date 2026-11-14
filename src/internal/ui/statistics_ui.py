"""Streamlit controls and tables for committed usage measurements."""

from datetime import datetime, timedelta, timezone
from dataclasses import replace
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import plotly.express as px
import streamlit as st

from internal.ui.exports import csv_bytes
from internal.analytics.usage_statistics import StatsRequest, delete_marker, list_markers, save_marker


def marker_controls(writer):
    """Render saved marker selection and management controls."""
    markers = list_markers(writer.connection)
    by_id = {marker.marker_id: marker for marker in markers}
    if "new_marker_default_timestamp" not in st.session_state:
        st.session_state["new_marker_default_timestamp"] = datetime.now(timezone.utc).isoformat()
    with st.sidebar.expander("Saved time markers"):
        choice = st.selectbox("Marker", ["None"] + list(by_id),
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
    return selected


def display_timezone():
    """Select an IANA time zone for report bounds and bucket labels."""
    zone = st.sidebar.text_input("Display time zone", value="UTC")
    try:
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        st.sidebar.error("Enter a valid IANA time zone, such as Europe/Sofia.")
        st.stop()
    return zone


def _number(value, suffix=""):
    if value is None:
        return "Unknown"
    return (f"{value:,.1f}" if isinstance(value, float) else f"{value:,}") + suffix


def _row(measurement, view=None):
    return {
        "Measurement": view or "Summary",
        "Scope": measurement.scope,
        "Start": measurement.start.isoformat() if measurement.start is not None else None,
        "End": measurement.end.isoformat() if measurement.end is not None else None,
        "Project": measurement.project,
        "Agent": measurement.agent if view not in {"Model", "Session"} else None,
        "Model": measurement.agent if view == "Model" else None,
        "Session": measurement.agent if view == "Session" else None,
        "Time": measurement.bucket.isoformat() if measurement.bucket is not None else None,
        "Total tokens": measurement.totals["total_tokens"],
        "Input tokens": measurement.totals["input_tokens"],
        "Output tokens": measurement.totals["output_tokens"],
        "Cached input": measurement.totals["cached_input_tokens"],
        "Non-cached input": measurement.totals["non_cached_input_tokens"],
        "Cache-write input": measurement.totals["cache_write_input_tokens"],
        "Reasoning output": measurement.totals["reasoning_output_tokens"],
        "Cache %": measurement.cache_percentage,
        "Daily average": measurement.average_daily_tokens,
        "Subagent share %": measurement.subagent_share,
        "Coverage": measurement.coverage,
        "Sessions": measurement.sessions,
        "Agents": measurement.agents,
        "Empty window": measurement.empty_window,
    }


def render_statistics(writer, calculator, selection, zone, marker, project_keys, selected_agent, record_ids=None):
    """Calculate and render both scopes and a selected breakdown."""
    start = pd.Timestamp(selection.start_date, tz=zone).tz_convert("UTC") if selection.start_date else None
    end = (pd.Timestamp(selection.end_date + timedelta(days=1), tz=zone).tz_convert("UTC")
           if selection.end_date else None)
    bucket = st.radio("Time aggregation", ["hourly", "daily", "weekly", "monthly"], index=1, horizontal=True)
    grouping = st.radio("Agent grouping", ["thread", "name"], horizontal=True)
    request = StatsRequest(start=start, end=end, time_zone=zone, bucket=bucket, agent_grouping=grouping,
                           marker=marker, projects=project_keys, models=selection.models,
                           sessions=selection.sessions, roles=selection.agent_roles,
                           agents=frozenset({selected_agent}) if selected_agent != "All agents" else None,
                           record_ids=record_ids)
    result = calculator.calculate(request)
    full_scope = result["Full selected period"][0]
    request = replace(request, resolved_start=full_scope.start, resolved_end=full_scope.end)
    view = st.selectbox("Usage view", ["Project over time", "Agent over time", "Agent by project", "Model", "Session"])
    export_rows = []
    for scope_index, (scope, (summary, groups)) in enumerate(result.items()):
        st.subheader(scope)
        if marker and scope != "Full selected period":
            st.caption(f"Marker: {pd.Timestamp(marker.timestamp).tz_convert(zone).isoformat()}")
        export_rows.append(_row(summary))
        if summary.empty_window:
            st.info("No time in range")
            continue
        start_label = summary.start.tz_convert(zone).isoformat() if summary.start is not None else "Unknown"
        end_label = summary.end.tz_convert(zone).isoformat() if summary.end is not None else "Unknown"
        st.caption(f"Effective period: {start_label} to {end_label} (end exclusive). Coverage: {summary.coverage}.")
        columns = st.columns(5)
        columns[0].metric("Total tokens", _number(summary.totals["total_tokens"]))
        columns[1].metric("Input tokens", _number(summary.totals["input_tokens"]))
        columns[2].metric("Output tokens", _number(summary.totals["output_tokens"]))
        columns[3].metric("Cache percentage", _number(summary.cache_percentage, "%"))
        columns[4].metric("Daily average", _number(summary.average_daily_tokens))
        extra_columns = st.columns(2)
        extra_columns[0].metric("Processing speed", "Unknown")
        extra_columns[1].metric("Subagent share", _number(summary.subagent_share, "%"))
        st.caption(f"Sessions: {summary.sessions:,} · Agent threads: {summary.agents:,}")
        st.caption("Legacy intervals crossing a boundary and potentially overlapping agent counters can make coverage partial.")
        components = [{"Component": label, "Tokens": summary.totals[field]} for label, field in
                      (("Cached input", "cached_input_tokens"), ("Non-cached input", "non_cached_input_tokens"),
                       ("Output", "output_tokens"))]
        if any(item["Tokens"] is not None for item in components):
            st.plotly_chart(px.bar(pd.DataFrame(components), x="Component", y="Tokens"),
                            use_container_width=True, key=f"components_{scope_index}")
        rows = [_row(item, view) for item in groups[view]]
        export_rows.extend(rows)
        if rows:
            table = pd.DataFrame(rows)
            x = {"Project over time": "Time", "Agent over time": "Time", "Agent by project": "Agent",
                 "Model": "Model", "Session": "Session"}[view]
            color = {"Project over time": "Project", "Agent over time": "Agent", "Agent by project": "Project",
                     "Model": "Model", "Session": "Session"}[view]
            if table["Total tokens"].notna().any():
                chart = table.copy()
                chart[color] = chart[color].fillna("Unknown")
                chart[x] = chart[x].fillna("Unknown")
                st.plotly_chart(px.bar(chart, x=x, y="Total tokens", color=color, hover_data=["Coverage"]),
                                use_container_width=True, key=f"usage_{scope_index}")
            st.dataframe(table, hide_index=True, use_container_width=True)
        else:
            st.info("No usage matches this scope.")
    columns = {name: name.lower().replace(" ", "_").replace("%", "percentage") for name in
               ("Measurement", "Scope", "Start", "End", "Project", "Agent", "Model", "Session", "Time", "Total tokens", "Input tokens",
                "Output tokens", "Cached input", "Non-cached input", "Cache-write input", "Reasoning output",
                "Cache %", "Daily average", "Subagent share %", "Coverage", "Sessions", "Agents", "Empty window")}
    st.download_button("Download usage CSV", csv_bytes(export_rows, columns), file_name="usage.csv", mime="text/csv")
    return request, calculator, result
