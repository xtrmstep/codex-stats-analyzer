"""Streamlit controls and tables for committed usage measurements."""

from datetime import datetime
from dataclasses import replace

import pandas as pd
import plotly.express as px
import streamlit as st

from internal.ui.exports import csv_bytes
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


def _row(measurement, view=None):
    return {
        "Measurement": view or "Summary",
        "Scope": measurement.scope,
        "Start": measurement.start.isoformat() if measurement.start is not None else None,
        "End": measurement.end.isoformat() if measurement.end is not None else None,
        "Project": measurement.project,
        "Agent": (measurement.agent or "Default") if view in {"Agent over time", "Agent by project"} else None,
        "Model": measurement.agent if view == "Model" else None,
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
        "Agents": measurement.agents,
        "Empty window": measurement.empty_window,
    }


def render_statistics(writer, calculator, selection, marker, project_keys, selected_agent,
                      bucket, view, sort_by, sort_order, record_ids=None):
    """Calculate and render both scopes and a selected breakdown."""
    request = StatsRequest(start_date=selection.start_date, end_date=selection.end_date,
                           bucket=bucket,
                           marker=marker, projects=project_keys, models=selection.models,
                           roles=selection.agent_roles,
                           agents=frozenset({selected_agent}) if selected_agent != "All agents" else None,
                           record_ids=record_ids)
    result = calculator.calculate(request)
    full_scope = result["Full selected period"][0]
    request = replace(request, resolved_start=full_scope.start, resolved_end=full_scope.end)
    export_rows = []
    for scope_index, (scope, (summary, groups)) in enumerate(result.items()):
        st.subheader(scope)
        if marker and scope != "Full selected period":
            st.caption(f"Marker: {marker.timestamp}")
        export_rows.append(_row(summary))
        if summary.empty_window:
            st.info("No time in range")
            continue
        start_label = summary.start.isoformat() if summary.start is not None else "Unknown"
        end_label = summary.end.isoformat() if summary.end is not None else "Unknown"
        date_label = f"Recorded dates: {selection.start_date or 'unbounded'} to {selection.end_date or 'unbounded'} (inclusive). " if selection.start_date or selection.end_date else ""
        st.caption(f"{date_label}Effective instants: {start_label} to {end_label}. Coverage: {summary.coverage}.")
        columns = st.columns(5)
        columns[0].metric("Total tokens", _number(summary.totals["total_tokens"]))
        columns[1].metric("Input tokens", _number(summary.totals["input_tokens"]))
        columns[2].metric("Output tokens", _number(summary.totals["output_tokens"]))
        columns[3].metric("Cache percentage", _number(summary.cache_percentage, "%"))
        columns[4].metric("Daily average", _number(summary.average_daily_tokens))
        extra_columns = st.columns(2)
        extra_columns[0].metric("Processing speed", "Unknown")
        extra_columns[1].metric("Subagent share", _number(summary.subagent_share, "%"))
        st.caption(f"Agent threads: {summary.agents:,}")
        st.caption("Legacy intervals crossing a boundary and potentially overlapping agent counters can make coverage partial.")
        components = [{"Component": label, "Tokens": summary.totals[field]} for label, field in
                      (("Cached input", "cached_input_tokens"), ("Non-cached input", "non_cached_input_tokens"),
                       ("Output", "output_tokens"))]
        if any(item["Tokens"] is not None for item in components):
            st.plotly_chart(px.bar(pd.DataFrame(components), x="Component", y="Tokens"),
                            use_container_width=True, key=f"components_{scope_index}")
        rows = [_row(item, view) for item in groups[view]]
        if sort_by == "Total tokens":
            known = sorted((row for row in rows if row["Total tokens"] is not None),
                           key=lambda row: row["Total tokens"], reverse=sort_order == "Descending")
            rows = known + [row for row in rows if row["Total tokens"] is None]
        else:
            rows.sort(key=lambda row: tuple(str(row[field] or "").casefold()
                                            for field in ("Project", "Agent", "Model", "Time")),
                      reverse=sort_order == "Descending")
        export_rows.extend(rows)
        if rows:
            table = pd.DataFrame(rows)
            x = {"Project over time": "Time", "Agent over time": "Time", "Agent by project": "Agent",
                 "Model": "Model"}[view]
            color = {"Project over time": "Project", "Agent over time": "Agent", "Agent by project": "Project",
                     "Model": "Model"}[view]
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
               ("Measurement", "Scope", "Start", "End", "Project", "Agent", "Model", "Time", "Total tokens", "Input tokens",
                "Output tokens", "Cached input", "Non-cached input", "Cache-write input", "Reasoning output",
                "Cache %", "Daily average", "Subagent share %", "Coverage", "Agents", "Empty window")}
    st.download_button("Download usage CSV", csv_bytes(export_rows, columns), file_name="usage.csv", mime="text/csv")
    return request, calculator, result
