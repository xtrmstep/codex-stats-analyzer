"""Streamlit dashboard using the shared analytics contract."""

from dataclasses import replace
from datetime import date
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from internal.analytics.agents import analyze_agents
from internal.analytics.token_accounting import Total, calculate_increments
from internal.analytics.metrics import Filters, build_dataset, filter_dataset
from internal.ingestion.collection import CodexLogImporter, CodexLogReader, DatabaseWriter
from internal.ui.statistics_ui import display_timezone, marker_editor, marker_selector, render_statistics
from internal.analytics.usage_statistics import StatsCalculation
from internal.ui.exports import csv_bytes, SESSION_COLUMNS
from internal.ui.session_comparisons import render_session_comparisons


def _display(total, suffix=""):
    if total.value is None:
        return "Unknown"
    number = f"{total.value:,.1f}" if isinstance(total.value, float) else f"{total.value:,}"
    return f"{number}{suffix}" + (" (partial)" if not total.complete else "")


def _options(frame, column, label):
    values = sorted(frame[column].dropna().unique().tolist())
    selected = st.multiselect(label, values)
    return frozenset(selected) if selected else None


def render(sources):
    """Render the overview and selected session from local read-only sources."""
    page = st.sidebar.radio("Navigation", ["Overview", "Manual annotations"])
    date_mode = st.selectbox("Date range", ["All Time", "Custom range"])
    start = end = None
    range_ready = True
    if date_mode == "Custom range":
        bounds = st.date_input("Selected dates", (date.today(), date.today()))
        if len(bounds) == 2:
            start, end = bounds
        else:
            range_ready = False
    try:
        writer = DatabaseWriter()
    except (OSError, sqlite3.Error, ValueError) as exc:
        st.error(f"Usage database is unavailable: {exc}")
        return
    try:
        _render(sources, writer, page, start, end, range_ready)
    finally:
        writer.close()


def _render(sources, writer, page, start, end, range_ready):
    if page == "Manual annotations":
        marker_editor(writer)
        return

    configuration = st.container()
    with configuration:
        st.subheader("Overview configuration")
        refresh_requested = st.button("Refresh sources")
        zone = display_timezone()
        marker = marker_selector(writer)
        bucket = st.radio("Time aggregation", ["hourly", "daily", "weekly", "monthly"], index=1, horizontal=True)
        grouping = st.radio("Agent grouping", ["thread", "name"], horizontal=True)
        view = st.selectbox("Usage view", ["Project over time", "Agent over time", "Agent by project", "Model", "Session"])
        sort_by = st.selectbox("Sort by", ["Group", "Total tokens"])
        sort_order = st.radio("Sort order", ["Ascending", "Descending"], horizontal=True)

    reader = CodexLogReader()
    importer = CodexLogImporter(reader, writer)
    state = writer.connection.execute("SELECT initialized, needs_rebuild FROM import_state WHERE id = 1").fetchone()
    initialized = bool(state and state[0])
    needs_rebuild = bool(state and state[1])
    first_attempt = not initialized and not st.session_state.get("initial_import_attempted", False)
    if first_attempt or refresh_requested:
        st.session_state["initial_import_attempted"] = True
        successful, diagnostics = (importer.rebuild() if first_attempt and needs_rebuild and not refresh_requested
                                   else importer.refresh(sources))
        st.session_state["source_diagnostics"] = [(item.source, item.message, item.fatal) for item in diagnostics]
        st.session_state["source_refresh_failed"] = not successful
    for source, message, fatal in st.session_state.get("source_diagnostics", []):
        (st.error if fatal else st.warning)(f"{source}: {message}")
    state = writer.connection.execute("SELECT initialized FROM import_state WHERE id = 1").fetchone()
    if not state or not state[0]:
        st.warning("No published usage dataset is available. Use Refresh sources to retry.")
        return
    if st.session_state.get("source_refresh_failed", False):
        st.warning("Showing the last committed usage dataset.")
    try:
        report_calculator = StatsCalculation(writer.database_path)
    except (ValueError, OSError, sqlite3.Error) as exc:
        st.error(f"Published usage is unavailable: {exc}")
        return

    parsed = report_calculator.parsed
    accounting = calculate_increments(parsed.events)
    frame = build_dataset(parsed.events, accounting.increments)
    with configuration:
        projects = {(row["project_key"], row["source_working_directory"]) for row in report_calculator.rows
                    if row["project_key"] is not None}
        selected_projects = st.multiselect("Projects", sorted({row[0] for row in projects}))
        project_keys = frozenset(selected_projects) if selected_projects else None
        source_projects = frozenset(row[1] for row in projects if row[0] in selected_projects and row[1])
        selection = Filters(start_date=start, end_date=end, time_zone=zone,
                            projects=source_projects if project_keys is not None else None,
                            models=_options(frame, "model", "Models"),
                            sessions=_options(frame, "session", "Sessions"),
                            agent_roles=_options(frame, "agent_role", "Agent roles"))
        selected = filter_dataset(frame, selection) if range_ready else frame.iloc[0:0].copy()
        available_agents = sorted(selected["agent"].dropna().unique().tolist())
        selected_agent = st.selectbox("Agent", ["All agents"] + available_agents)

    if not range_ready:
        st.info("Select both dates for the reporting range.")
        return
    if selected_agent != "All agents":
        selected = selected.loc[selected["agent"] == selected_agent].copy()
    report_request, report_calculator, report_result = render_statistics(
        writer, report_calculator, selection, zone, marker, project_keys, selected_agent,
        bucket, grouping, view, sort_by, sort_order
    )
    if selected.empty:
        st.info("No observed events match the selected filters.")
    else:
        st.subheader("Sessions")
        sessions = sorted(selected["session"].dropna().unique().tolist())
        session_metrics = {item.agent: item for item in report_result["Full selected period"][1]["Session"]}
        session_rows = []
        for key in sessions:
            value = session_metrics.get(key)
            times = selected.loc[selected["session"] == key, "timestamp"].dropna()
            session_rows.append({"Session": key, "Tokens": value.totals["total_tokens"] if value else None,
                                 "Input": value.totals["input_tokens"] if value else None,
                                 "Output": value.totals["output_tokens"] if value else None,
                                 "Coverage": value.coverage if value else "unknown",
                                 "Provenance": "committed usage records",
                                 "Agents": value.agents if value else 0,
                                 "First observed UTC": times.min().isoformat() if not times.empty else None,
                                 "Last observed UTC": times.max().isoformat() if not times.empty else None})
        if sort_by == "Total tokens":
            known = sorted((row for row in session_rows if row["Tokens"] is not None),
                           key=lambda row: row["Tokens"], reverse=sort_order == "Descending")
            session_rows = known + [row for row in session_rows if row["Tokens"] is None]
        else:
            session_rows.sort(key=lambda row: str(row["Session"]).casefold(), reverse=sort_order == "Descending")
        st.dataframe(pd.DataFrame(session_rows), hide_index=True, use_container_width=True)
        st.download_button("Download filtered sessions CSV", csv_bytes(session_rows, SESSION_COLUMNS),
                           file_name="sessions.csv", mime="text/csv")
        st.caption("CSV uses UTF-8 with BOM, UTC ISO 8601 timestamps, blank unknown values and token/second units indicated in the column names.")
        session_ids = sorted(selected["session"].dropna().unique().tolist())
        if session_ids:
            session_id = st.selectbox("Session detail", session_ids)
            thread_rows = [row for row in report_calculator.threads if row["session_id"] == session_id]
            execution_ids = {row["execution_id"] for row in thread_rows}
            roots = [row["thread_id"] for row in thread_rows if row["parent_execution_id"] not in execution_ids]
            if roots:
                root = st.selectbox("Root agent", roots)
                details(root, selected, parsed.events, accounting.increments, start is not None or end is not None,
                        report_calculator, replace(report_request, sessions=frozenset({session_id}), marker=None))
    render_session_comparisons(report_calculator, report_request, selected)
    with st.expander(f"Parsing and accounting diagnostics ({len(parsed.diagnostics) + len(accounting.diagnostics)})"):
        for item in parsed.diagnostics:
            st.write(f"{item.source}:{item.line or '-'} — {item.message}")
        for item in accounting.diagnostics:
            st.write(item)


def details(root, selected, events, increments, date_filter_active=False, calculator=None, report_request=None):
    """Show hierarchy as context, while all usage follows active filters."""
    def measurement(agent_ids):
        allowed = set(agent_ids)
        if report_request.agents is not None:
            allowed &= set(report_request.agents)
        request = replace(report_request, agents=frozenset(allowed))
        return calculator.calculate(request)["Full selected period"][0]

    hierarchy = analyze_agents(root, events, increments)
    st.subheader("Agent hierarchy")
    st.caption("Hierarchy is context from all evidence; token metrics below respect the active filters. Unlinked agents are not assigned to this tree.")
    if root in hierarchy.agents:
        stack = [(root, 0)]
        while stack:
            agent_id, depth = stack.pop()
            agent = hierarchy.agents[agent_id]
            st.text(f"{'  ' * depth}{agent_id}  |  {agent.role or 'role unknown'}  |  {agent.model or 'model unknown'}")
            stack.extend((child, depth + 1) for child in reversed(hierarchy.children[agent_id]))
    if hierarchy.unlinked:
        st.write("Unlinked agents: " + ", ".join(hierarchy.unlinked))
    tree_ids = set(hierarchy.agents) - set(hierarchy.unlinked)
    rows = []
    timeline = []
    selected_references = set(selected["reference"])
    selected_agents = set(selected["agent"].dropna())
    for agent_id in sorted(tree_ids):
        agent = hierarchy.agents[agent_id]
        totals = measurement({agent_id})
        rows.append({"Agent": agent_id, "Parent": agent.parent_id, "Role": agent.role, "Nickname": agent.nickname,
                     "Model": agent.model, "Status": agent.status,
                     "Tokens": _display(Total(totals.totals["total_tokens"], totals.coverage == "complete")),
                     "Cache %": _display(Total(totals.cache_percentage, totals.coverage == "complete"), "%"),
                     "First observed": agent.activity.first, "Last observed": agent.activity.last})
        activity = agent.activity
        times = pd.to_datetime(
            [event.timestamp for event in events if (event.thread_id or event.session_id) == agent_id
             and event.reference in selected_references and event.timestamp],
            format="mixed", utc=True, errors="coerce")
        times = times[~times.isna()]
        if len(times) > 1 and times.min() < times.max():
            timeline.append({"Agent": agent_id, "Start": times.min(), "End": times.max(), "Evidence": "Observed activity span"})
        if (agent_id in selected_agents and not date_filter_active
                and activity.verified_reference in selected_references
                and activity.verified_start and activity.verified_end):
            timeline.append({"Agent": agent_id, "Start": activity.verified_start, "End": activity.verified_end, "Evidence": "Verified execution interval"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    main_metrics = measurement({root})
    st.write(f"Main agent tokens under filters: {_display(Total(main_metrics.totals['total_tokens'], main_metrics.coverage == 'complete'))}")
    descendant_ids = tree_ids - {root}
    sub_metrics = measurement(descendant_ids)
    comparison = [{"Agent group": label, "Tokens": item.totals["total_tokens"],
                   "Coverage": item.coverage}
                  for label, item in (("Main", main_metrics), ("Subagents", sub_metrics))]
    if any(item["Tokens"] is not None for item in comparison):
        st.plotly_chart(px.bar(pd.DataFrame(comparison), x="Agent group", y="Tokens", color="Coverage"), use_container_width=True)
    st.write("Subagent share: Unknown — parent and child counter scope is unresolved. Main and subagent figures may overlap and must not be added.")
    st.caption("Timeline spans use matching events only and do not establish execution duration. The hierarchy table shows full context. Verified intervals are omitted when a date filter is active because their boundaries may lie outside it.")
    if timeline:
        timeline_frame = pd.DataFrame(timeline)
        for column in ("Start", "End"):
            timeline_frame[column] = pd.to_datetime(timeline_frame[column], format="mixed", utc=True, errors="coerce")
        invalid = timeline_frame["Start"].isna() | timeline_frame["End"].isna() | (timeline_frame["End"] < timeline_frame["Start"])
        if invalid.any():
            st.warning(f"{invalid.sum()} activity interval(s) have invalid endpoints and cannot be plotted.")
        timeline_frame = timeline_frame.loc[~invalid]
        if not timeline_frame.empty:
            st.plotly_chart(px.timeline(timeline_frame, x_start="Start", x_end="End", y="Agent", color="Evidence"), use_container_width=True)
        else:
            st.info("No activity intervals with two valid endpoints.")
    else:
        st.info("No activity intervals with two known endpoints.")
    selected_skills = [skill for skill in hierarchy.skills if skill["agent_id"] in tree_ids
                       and skill["agent_id"] in selected_agents and skill["reference"] in selected_references]
    if selected_skills:
        st.write("Explicit skill evidence", pd.DataFrame(selected_skills))
    if hierarchy.diagnostics:
        with st.expander("Hierarchy limitations"):
            for item in hierarchy.diagnostics:
                st.write(item)














