"""Streamlit controls and tables for committed usage measurements."""

from dataclasses import replace
from datetime import datetime
import os

from dateutil import tz
import pandas as pd
import plotly.express as px
import streamlit as st

from internal.analytics.usage_statistics import StatsRequest, delete_marker, list_markers, save_marker


def marker_selector(writer, disabled=False):
    """Select an existing marker for the Overview report."""
    markers = list_markers(writer.connection)
    by_id = {marker.marker_id: marker for marker in markers}
    if st.session_state.get("overview_marker", "None") not in by_id:
        st.session_state["overview_marker"] = "None"
    choice = st.selectbox("Saved time marker", ["None"] + list(by_id),
                          format_func=lambda key: by_id[key].name if key in by_id else key,
                          key="overview_marker", disabled=disabled)
    return by_id.get(choice)


def _local_timezone():
    """Return the host's local zone with daylight-saving rules."""
    return tz.tzwinlocal() if os.name == "nt" else tz.gettz()


def _local_marker_timestamp(day, clock, zone):
    """Resolve a local wall time only when it identifies exactly one instant."""
    local = datetime.combine(day, clock).replace(tzinfo=zone)
    if not tz.datetime_exists(local) or tz.datetime_ambiguous(local):
        raise ValueError("Choose a local time that exists and is not repeated by a daylight-saving change.")
    return local.isoformat()


def marker_editor(writer):
    """Create, edit, or delete saved markers."""
    markers = list_markers(writer.connection)
    by_id = {marker.marker_id: marker for marker in markers}
    zone = _local_timezone()
    if st.button("Add new"):
        st.session_state["marker_editor_generation"] = st.session_state.get("marker_editor_generation", 0) + 1
        st.session_state["marker_editor_target"] = "new"
        st.session_state["marker_editor_initial"] = datetime.now().astimezone(zone).isoformat()
    if markers:
        widths = [2, 3, 4, 3]
        name_column, timestamp_column, description_column, actions_column = st.columns(widths)
        name_column.markdown("**Name**")
        timestamp_column.markdown("**Timestamp**")
        description_column.markdown("**Description**")
        actions_column.markdown("**Actions**")
        ordered = sorted(markers, key=lambda item: datetime.fromisoformat(item.timestamp))
        for item in ordered:
            name_column, timestamp_column, description_column, actions_column = st.columns(widths)
            name_column.text(item.name)
            timestamp_column.text(datetime.fromisoformat(item.timestamp).astimezone(zone).strftime("%Y-%m-%d %H:%M:%S"))
            description_column.text(item.description)
            edit_column, delete_column = actions_column.columns(2)
            if edit_column.button("Edit", key=f"marker_edit_{item.marker_id}"):
                st.session_state["marker_editor_generation"] = st.session_state.get("marker_editor_generation", 0) + 1
                st.session_state["marker_editor_target"] = item.marker_id
            if delete_column.button("Delete", key=f"marker_delete_{item.marker_id}"):
                delete_marker(writer, item.marker_id)
                if st.session_state.get("marker_editor_target") == item.marker_id:
                    st.session_state.pop("marker_editor_target", None)
                st.rerun()
    else:
        st.info("No saved time markers")
    target = st.session_state.get("marker_editor_target")
    if target is None:
        return
    selected = by_id.get(target)
    if target != "new" and selected is None:
        st.session_state.pop("marker_editor_target", None)
        return
    initial_timestamp = selected.timestamp if selected else st.session_state["marker_editor_initial"]
    initial = datetime.fromisoformat(initial_timestamp).astimezone(zone)
    displayed_time = initial.time().replace(tzinfo=None, microsecond=0)
    generation = st.session_state["marker_editor_generation"]
    with st.form("marker_editor"):
        name = st.text_input("Name", value=selected.name if selected else "", key=f"marker_name_{generation}")
        description = st.text_area(
            "Description", value=selected.description if selected else "", key=f"marker_description_{generation}"
        )
        st.caption(f"Local time zone: {initial.tzname()}")
        day = st.date_input("Date", value=initial.date(), key=f"marker_date_{generation}")
        clock = st.time_input("Time", value=displayed_time, step=1, key=f"marker_time_{generation}")
        save = st.form_submit_button("Save")
    if save:
        try:
            timestamp = (initial_timestamp if selected and day == initial.date() and clock == displayed_time
                         else _local_marker_timestamp(day, clock, zone))
            save_marker(writer, name, timestamp, selected.marker_id if selected else None, description=description)
            st.session_state.pop("marker_editor_target", None)
            st.rerun()
        except (ValueError, OverflowError) as exc:
            st.error(str(exc))


def _number(value, suffix=""):
    if value is None:
        return "Unknown"
    return (f"{value:,.1f}" if isinstance(value, float) else f"{value:,}") + suffix


def _kpi_values(summary):
    """Format each KPI in table order for a reporting window."""
    return [
        _number(summary.totals["total_tokens"]),
        _number(summary.totals["input_tokens"]),
        _number(summary.totals["output_tokens"]),
        _number(summary.totals["cached_input_tokens"]),
        _number(summary.totals["non_cached_input_tokens"]),
        _number(summary.cache_percentage, "%"),
        _number(summary.average_daily_tokens),
    ]


def _row(measurement, view):
    return {
        "Project": measurement.project,
        "Agent": (measurement.agent or "Default") if view in {"Agent over time", "Agent by project", "By agent"} else None,
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
        names = _name_key(measurement.project if view == "Project over time" else measurement.agent)
        return (measurement.bucket is None, measurement.bucket or pd.Timestamp.max, *names)
    if view == "Agent by project":
        return _name_key(measurement.project) + _name_key(measurement.agent or "Default")
    if view == "By project":
        return _name_key(measurement.project)
    return _name_key(measurement.agent)


def _comparison_result(calculator, request, bounds, agents):
    """Calculate the preceding period without applying the saved marker."""
    if bounds is None:
        return None
    comparison_request = replace(request, start_date=bounds[0], end_date=bounds[1],
                                 agents=agents, marker=None)
    summary, groups = calculator.calculate(comparison_request)["Full selected period"]
    return bounds, summary, groups


def _render_chart(groups, title, group_key, series, scope_index, period):
    """Render one chart or its empty state."""
    ordered = sorted(groups[group_key], key=lambda item: _measurement_key(item, title))
    rows = [_row(item, title) for item in ordered]
    if not rows or not any(row["Total tokens"] is not None for row in rows):
        st.info("No plottable usage for this chart.")
        return
    chart = pd.DataFrame(rows)
    chart[series] = chart[series].fillna("Unknown")
    trend = title.endswith("over time")
    x = "Time" if trend else "Project" if title == "Agent by project" else series
    kwargs = {}
    if title == "Agent by project":
        chart["Project"] = chart["Project"].fillna("Unknown")
        kwargs["barmode"] = "group"
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
    if not trend and chart[x].astype(str).str.len().max() > 24:
        height = 310
    figure.update_layout(height=height, margin=dict(l=20, r=20, t=top_margin, b=35))
    figure.update_xaxes(automargin=True)
    figure.update_yaxes(automargin=True)
    st.plotly_chart(figure, use_container_width=True, key=f"usage_{scope_index}_{period}_{group_key}")


def render_statistics(calculator, selection, marker, project_keys, selected_agents, bucket,
                      comparison_bounds=None, comparison_agents=None):
    """Calculate and render each scope's seven usage breakdowns."""
    request = StatsRequest(start_date=selection.start_date, end_date=selection.end_date,
                           bucket=bucket,
                           marker=marker, projects=project_keys, models=selection.models,
                           roles=selection.agent_roles,
                           agents=selected_agents)
    result = calculator.calculate(request)
    comparison = _comparison_result(calculator, request, comparison_bounds, comparison_agents)
    for scope_index, (scope, (summary, groups)) in enumerate(result.items()):
        if scope != "Full selected period":
            st.subheader(scope)
            if marker:
                st.caption(f"Marker: {marker.timestamp}")
        if summary.empty_window:
            st.info("No time in range")
            continue
        if scope != "Full selected period":
            start_label = summary.start.isoformat() if summary.start is not None else "Unknown"
            end_label = summary.end.isoformat() if summary.end is not None else "Unknown"
            date_label = f"Recorded dates: {selection.start_date or 'unbounded'} to {selection.end_date or 'unbounded'} (inclusive). " if selection.start_date or selection.end_date else ""
            st.caption(f"{date_label}Effective instants: {start_label} to {end_label}. Coverage: {summary.coverage}.")
        kpis = [
            ("Total tokens",
             "Total tokens used for model input and output. `Input tokens + Output tokens`"),
            ("Input tokens",
             "Tokens sent to the model, including cached input. `Cached input + Non-cached input`"),
            ("Output tokens",
             "Tokens generated by the model. `sum(response output tokens)`"),
            ("Cached input",
             "Input tokens reused from cache. `sum(response cached input)`"),
            ("Non-cached input",
             "Input tokens not served from cache, where both counts are known. `Input tokens − Cached input`"),
            ("Cache percentage",
             "Share of input served from cache, where both counts are known. `100 × Cached input ÷ Input tokens`"),
            ("Daily average",
             "Average tokens per day over the reporting window. `Total tokens ÷ Elapsed days`"),
        ]
        table_key = f"overview_kpis_{scope_index}"
        previous_values = (_kpi_values(comparison[1])
                           if scope == "Full selected period" and comparison is not None else None)
        values = _kpi_values(summary)
        with st.container(key=table_key):
            st.markdown(f"""
                <style>
                .st-key-{table_key} table {{ width: 100%; table-layout: fixed; font-size: 14px; }}
                .st-key-{table_key} th, .st-key-{table_key} td {{
                    padding: 0.2rem 0.4rem; white-space: normal; overflow-wrap: anywhere;
                }}
                .st-key-{table_key} th:nth-child(1) {{ width: {20 if previous_values is not None else 24}%; }}
                .st-key-{table_key} th:nth-child(2) {{ width: 16%; }}
                .st-key-{table_key} th:nth-child(2), .st-key-{table_key} td:nth-child(2) {{ text-align: right; }}
                {f'.st-key-{table_key} th:nth-child(3), .st-key-{table_key} td:nth-child(3) {{ text-align: right; width: 16%; }}' if previous_values is not None else ''}
                .st-key-{table_key} code {{
                    font-size: 14px; white-space: normal; overflow-wrap: anywhere;
                }}
                </style>
            """, unsafe_allow_html=True)
            if previous_values is not None:
                header = "| Name | Value | Previous period | Description |\n| --- | --- | --- | --- |\n"
                rows = (f"| {name} | {value} | {previous} | {description} |"
                        for (name, description), value, previous in zip(kpis, values, previous_values))
            else:
                header = "| Name | Value | Description |\n| --- | --- | --- |\n"
                rows = (f"| {name} | {value} | {description} |"
                        for (name, description), value in zip(kpis, values))
            st.markdown(header + "\n".join(rows))
        sections = (
            ("Token consumption over time", (
                ("Project over time", "Project over time", "Project"),
                ("Agent over time", "Agent over time", "Agent"),
                ("Model over time", "Model over time", "Model"))),
            ("Total token consumption", (
                ("By model", "Model", "Model"),
                ("By project", "By project", "Project"),
                ("By agent", "By agent", "Agent"),
                ("Agent by project", "Agent by project", "Agent"))),
        )
        if scope == "Full selected period" and comparison is not None:
            left, right = st.columns(2)
            with left:
                st.markdown("**Selected period**")
                st.caption(f"{selection.start_date} to {selection.end_date} (inclusive)")
            with right:
                st.markdown("**Previous period**")
                st.caption(f"{comparison[0][0]} to {comparison[0][1]} (inclusive)")
        for section, charts in sections:
            st.subheader(section)
            for title, group_key, series in charts:
                heading = f"By {series}" if title.endswith("over time") else title
                st.markdown(f"##### {heading}")
                if scope == "Full selected period" and comparison is not None:
                    left, right = st.columns(2)
                    with left:
                        _render_chart(groups, title, group_key, series, scope_index, "selected")
                    with right:
                        _render_chart(comparison[2], title, group_key, series, scope_index, "previous")
                else:
                    _render_chart(groups, title, group_key, series, scope_index, "selected")
