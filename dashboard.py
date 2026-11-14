"""Streamlit dashboard using the shared analytics contract."""

from pathlib import Path
from dataclasses import replace
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from agents import analyze_agents
from analytics import Total, calculate_increments
from metrics import Filters, build_dataset, filter_dataset
from collection import CodexLogImporter, CodexLogReader, DatabaseWriter
from statistics_ui import display_timezone, marker_controls, render_statistics
from usage_statistics import StatsCalculation
from annotations import MetadataStore, StorageError, missing_sessions
from labels_ui import manage
from labels import assigned, matches, run_labels
from run_ui import manage_runs, select_runs, run_summary
from experiment_ui import render_experiments
from exports import csv_bytes, SESSION_COLUMNS, RUN_COLUMNS
from runs import calculate_run


def _display(total, suffix=""):
    if total.value is None:
        return "Unknown"
    number = f"{total.value:,.1f}" if isinstance(total.value, float) else f"{total.value:,}"
    return f"{number}{suffix}" + (" (partial)" if not total.complete else "")


def _options(frame, column, label):
    values = sorted(frame[column].dropna().unique().tolist())
    selected = st.sidebar.multiselect(label, values)
    return frozenset(selected) if selected else None


def render(sources):
    """Render the overview and selected session from local read-only sources."""
    try:
        writer = DatabaseWriter()
    except (OSError, sqlite3.Error, ValueError) as exc:
        st.error(f"Usage database is unavailable: {exc}")
        return
    try:
        _render(sources, writer)
    finally:
        writer.close()


def _render(sources, writer):
    refresh_requested = st.sidebar.button("Refresh sources")
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
    store = MetadataStore(Path(__file__).resolve().parent / "data" / "annotations.json", "annotations")
    try:
        snapshot = store.load()
    except StorageError as exc:
        st.error(f"Manual labels unavailable: {exc}")
        snapshot = None
    if snapshot is not None:
        manage(store, snapshot, sorted(frame["session"].dropna().unique().tolist()))
        manage_runs(store, snapshot, parsed.events, accounting.increments)
    if snapshot is not None:
        missing = missing_sessions(snapshot, {event.session_id for event in parsed.events})
        if missing:
            st.warning("Annotations reference unavailable sessions: " + ", ".join(sorted(missing)))
        unresolved = [(run["name"], issue) for run in snapshot.data["runs"]
                      for issue in calculate_run(run, parsed.events, accounting.increments).diagnostics
                      if "missing" in issue.lower() or "unavailable" in issue.lower() or "outside observed" in issue.lower()]
        if unresolved:
            with st.expander("Unavailable run references"):
                for name, issue in unresolved:
                    st.write(f"{name}: {issue}")
    st.sidebar.header("Filters")
    zone = display_timezone()
    marker = marker_controls(writer)
    st.sidebar.caption("Manual filters select matching session usage and matching run intervals. Run boundaries are estimated; overlapping runs are counted once globally.")
    use_dates = st.sidebar.checkbox("Filter dates")
    start = end = None
    if use_dates:
        dates = frame["timestamp"].dropna().dt.tz_convert(zone)
        if dates.empty:
            st.sidebar.info("No timestamped events are available.")
        else:
            bounds = st.sidebar.date_input("Date range", (dates.min().date(), dates.max().date()))
            if len(bounds) == 2:
                start, end = bounds
    definitions = {item["id"]: item for item in snapshot.data["labels"]} if snapshot else {}
    chosen_labels = st.sidebar.multiselect("Manual labels", list(definitions), format_func=lambda item: definitions[item]["name"])
    label_mode = st.sidebar.radio("Match labels", ["all", "any"], horizontal=True)
    task_values = sorted({item.get("value") for item in definitions.values() if item.get("key", "").casefold() == "task_type" and item.get("value")})
    mode_values = sorted({item.get("value") for item in definitions.values() if item.get("key", "").casefold() == "execution_mode" and item.get("value")})
    if snapshot:
        task_values = sorted(set(task_values) | {run["task_type"] for run in snapshot.data["runs"] if run.get("task_type")})
        mode_values = sorted(set(mode_values) | {run["execution_mode"] for run in snapshot.data["runs"] if run.get("execution_mode")})
    task_types = st.sidebar.multiselect("Manual task type", task_values)
    execution_modes = st.sidebar.multiselect("Manual execution mode", mode_values)
    projects = {(row["project_key"], row["source_working_directory"]) for row in report_calculator.rows
                if row["project_key"] is not None}
    selected_projects = st.sidebar.multiselect("Projects", sorted({row[0] for row in projects}))
    project_keys = frozenset(selected_projects) if selected_projects else None
    source_projects = frozenset(row[1] for row in projects if row[0] in selected_projects and row[1])
    selection = Filters(start_date=start, end_date=end, time_zone=zone,
                        label_ids=frozenset(chosen_labels) if chosen_labels else None, label_mode=label_mode,
                        task_types=frozenset(task_types) if task_types else None,
                        execution_modes=frozenset(execution_modes) if execution_modes else None,
                        projects=source_projects if project_keys is not None else None,
                        models=_options(frame, "model", "Models"),
                        sessions=_options(frame, "session", "Sessions"),
                        agent_roles=_options(frame, "agent_role", "Agent roles"))
    chosen_runs = st.sidebar.multiselect("Runs", [run["id"] for run in snapshot.data["runs"]] if snapshot else [],
                                       format_func=lambda identifier: next((run["name"] for run in snapshot.data["runs"] if run["id"] == identifier), identifier))
    base_selection = replace(selection, label_ids=None, task_types=None, execution_modes=None)
    selected = filter_dataset(frame, base_selection)
    available_agents = sorted(selected["agent"].dropna().unique().tolist())
    selected_agent = st.sidebar.selectbox("Agent", ["All agents"] + available_agents)
    if selected_agent != "All agents":
        selected = selected.loc[selected["agent"] == selected_agent].copy()
    run_matches = select_runs(snapshot.data, parsed.events, accounting.increments, selection, selected) if snapshot else []
    if chosen_runs:
        run_matches = [item for item in run_matches if item[0]["id"] in chosen_runs]
    manual_active = any(value is not None for value in (selection.label_ids, selection.task_types, selection.execution_modes))
    if chosen_runs or manual_active:
        indices = set()
        if manual_active and not chosen_runs and snapshot:
            for session in selected["session"].dropna().unique():
                labels = assigned(snapshot.data, "session", session)
                if matches(snapshot.data, labels, selection.label_ids, selection.label_mode, selection.task_types, selection.execution_modes):
                    indices.update(selected.index[selected["session"] == session])
        for _, _, run_frame in run_matches:
            indices.update(run_frame.index)
        selected = selected.loc[selected.index.isin(indices)].copy()
        selected.attrs["manual_filter"] = True
        selected.attrs["run_filter"] = True
    selected_record_ids = None
    if chosen_runs or manual_active:
        references = set(selected["reference"])
        selected_record_ids = frozenset(event.record_id for event in parsed.events
                                        if event.reference in references and event.record_id)
    report_request, report_calculator, report_result = render_statistics(
        writer, report_calculator, selection, zone, marker, project_keys, selected_agent, selected_record_ids
    )
    run_rows, run_mean, run_median = run_summary(run_matches, parsed.events, snapshot.data if snapshot else None)
    run_columns = st.columns(3)
    run_columns[0].metric("Runs", len(run_rows))
    run_columns[1].metric("Average tokens per run", f"{run_mean:,.1f}" if run_mean is not None else "Unknown")
    run_columns[2].metric("Median tokens per run", f"{run_median:,.1f}" if run_median is not None else "Unknown")
    st.caption("Run averages and medians include known values only. Run attribution is estimated.")
    if selected.empty:
        st.info("No observed events match the selected filters.")
    else:
        st.subheader("Runs")
        st.dataframe(pd.DataFrame(run_rows), hide_index=True, use_container_width=True)
        st.download_button("Download filtered runs CSV", csv_bytes(run_rows, RUN_COLUMNS), file_name="runs.csv", mime="text/csv")
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
        st.dataframe(pd.DataFrame(session_rows), hide_index=True, use_container_width=True)
        st.download_button("Download filtered sessions CSV", csv_bytes(session_rows, SESSION_COLUMNS), file_name="sessions.csv", mime="text/csv")
        st.caption("CSV uses UTF-8 with BOM, UTC ISO 8601 timestamps, blank unknown values and token/second units indicated in the column names.")
        session_ids = sorted(selected["session"].dropna().unique().tolist())
        if session_ids:
            session_id = st.selectbox("Session detail", session_ids)
            thread_rows = [row for row in report_calculator.threads if row["session_id"] == session_id]
            execution_ids = {row["execution_id"] for row in thread_rows}
            roots = [row["thread_id"] for row in thread_rows if row["parent_execution_id"] not in execution_ids]
            if roots:
                root = st.selectbox("Root agent", roots)
                details(root, selected, parsed.events, accounting.increments, use_dates,
                        report_calculator, replace(report_request, sessions=frozenset({session_id}), marker=None))
    if snapshot is not None:
        render_experiments(snapshot.data, parsed.events, accounting.increments, selected, selection, selected_agent, chosen_runs)
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














