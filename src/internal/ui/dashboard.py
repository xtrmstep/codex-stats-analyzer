"""Streamlit dashboard using the shared analytics contract."""

from datetime import date, timedelta
import sqlite3

import streamlit as st

from internal.analytics.metrics import Filters, build_dataset, filter_dataset
from internal.ingestion.collection import CodexLogImporter, CodexLogReader, DatabaseWriter
from internal.ui.statistics_ui import marker_editor, marker_selector, render_statistics
from internal.ui.agent_names_ui import agent_name_editor
from internal.analytics.usage_statistics import StatsCalculation, reporting_agent_name


def _options(frame, column, label):
    values = sorted(frame[column].dropna().unique().tolist())
    selected = st.multiselect(label, values)
    return frozenset(selected) if selected else None


def _unrestricted_label(label, options):
    """Keep the default label distinct from actual names or titles."""
    if label not in options:
        return label
    base = f"{label} (no filter)"
    candidate = base
    suffix = 2
    while candidate in options:
        candidate = f"{base} {suffix}"
        suffix += 1
    return candidate


def _date_limits(preset, today):
    """Resolve an Overview preset to inclusive local calendar dates."""
    monday = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    previous_month_end = month_start - timedelta(days=1)
    return {
        "Today": (today, today),
        "All Time": (None, None),
        "Last 7 days": (today - timedelta(days=6), today),
        "Last 30 days": (today - timedelta(days=29), today),
        "Current week": (monday, today),
        "Last week": (monday - timedelta(days=7), monday - timedelta(days=1)),
        "Current month": (month_start, today),
        "Last month": (previous_month_end.replace(day=1), previous_month_end),
    }[preset]


def render(sources):
    """Render the overview and selected session from local read-only sources."""
    page = st.sidebar.radio("Navigation", ["Overview", "Manual annotations"])
    try:
        writer = DatabaseWriter()
    except (OSError, sqlite3.Error, ValueError) as exc:
        st.error(f"Usage database is unavailable: {exc}")
        return
    try:
        _render(sources, writer, page)
    finally:
        writer.close()


def _render(sources, writer, page):
    if page == "Manual annotations":
        marker_editor(writer)
        agent_name_editor(writer)
        return

    refresh_columns = st.columns(2)
    incremental_requested = refresh_columns[0].button("Incremental refresh")
    full_requested = refresh_columns[1].button(
        "Full refresh from source",
        help="Replaces imported history with available source logs; saved markers and agent names are kept.",
    )
    with st.sidebar:
        st.subheader("Overview configuration")
        presets = ["Today", "Last 7 days", "Last 30 days", "All Time", "Current week", "Last week",
                   "Current month", "Last month"]
        today = date.today()
        limits = {name: _date_limits(name, today) for name in presets}

        def date_label(name):
            first, last = limits[name]
            if first is None:
                return name
            dates = first.isoformat() if name == "Today" else f"{first.isoformat()} to {last.isoformat()}"
            return f"{name} ({dates})"

        preset = st.selectbox("Date range", presets, index=presets.index("Last 7 days"),
                              format_func=date_label, key="overview_date_range")
        start, end = limits[preset]
        bucket = st.radio("Time aggregation", ["hourly", "daily", "weekly", "monthly"], index=1, horizontal=True)

    filters = st.sidebar.expander("Filters", expanded=True)
    with filters:
        marker = marker_selector(writer)

    reader = CodexLogReader()
    importer = CodexLogImporter(reader, writer)
    state = writer.connection.execute("SELECT initialized, needs_rebuild FROM import_state WHERE id = 1").fetchone()
    initialized = bool(state and state[0])
    needs_rebuild = bool(state and state[1])
    first_attempt = not initialized and not st.session_state.get("initial_import_attempted", False)
    if first_attempt or incremental_requested or full_requested:
        st.session_state["initial_import_attempted"] = True
        if full_requested:
            successful, diagnostics = importer.full_refresh(sources)
        elif incremental_requested or not needs_rebuild:
            successful, diagnostics = importer.refresh(sources)
        else:
            successful, diagnostics = importer.rebuild()
        st.session_state["source_diagnostics"] = [(item.source, item.message, item.fatal) for item in diagnostics]
        st.session_state["source_refresh_failed"] = not successful
    for source, message, fatal in st.session_state.get("source_diagnostics", []):
        (st.error if fatal else st.warning)(f"{source}: {message}")
    state = writer.connection.execute("SELECT initialized FROM import_state WHERE id = 1").fetchone()
    if not state or not state[0]:
        st.warning("No published usage dataset is available. Use Incremental refresh to retry.")
        return
    if st.session_state.get("source_refresh_failed", False):
        st.warning("Showing the last committed usage dataset.")
    try:
        report_calculator = StatsCalculation(writer.database_path)
    except (ValueError, OSError, sqlite3.Error) as exc:
        st.error(f"Published usage is unavailable: {exc}")
        return

    parsed = report_calculator.parsed
    frame = build_dataset(parsed.events)
    usage_diagnostics = [item for item in report_calculator.diagnostics if item.get("kind") == "usage"]
    with filters:
        projects = {(row["project_key"], row["source_working_directory"]) for row in report_calculator.rows
                    if row["project_key"] is not None}
        selected_projects = st.multiselect("Projects", sorted({row[0] for row in projects}))
        project_keys = frozenset(selected_projects) if selected_projects else None
        source_projects = frozenset(row[1] for row in projects if row[0] in selected_projects and row[1])
        selection = Filters(start_date=start, end_date=end,
                            projects=source_projects if project_keys is not None else None,
                            models=_options(frame, "model", "Models"),
                            agent_roles=_options(frame, "agent_role", "Agent roles"))
        selected = filter_dataset(frame, selection)
        available_pairs = set(zip(selected["session"], selected["agent"]))
        available_threads = [row for row in report_calculator.threads
                             if (row["session_id"], row["thread_id"]) in available_pairs]
        titles = {row["chat_title"] for row in available_threads if row["chat_title"]}
        all_chats_label = _unrestricted_label("All chats", titles)
        if st.session_state.get("overview_chat") not in titles:
            st.session_state["overview_chat"] = None
        selected_chat = st.selectbox("Chat", [None] + sorted(titles, key=lambda title: (title.casefold(), title)),
                                     format_func=lambda title: all_chats_label if title is None else title,
                                     key="overview_chat")
        if selected_chat is not None:
            available_threads = [row for row in available_threads if row["chat_title"] == selected_chat]
        names = {reporting_agent_name(row) for row in available_threads}
        all_agents_label = _unrestricted_label("All agents", names)
        if st.session_state.get("overview_agent") not in names:
            st.session_state["overview_agent"] = None
        selected_agent = st.selectbox("Agent", [None] + sorted(names, key=lambda name: (name.casefold(), name)),
                                      format_func=lambda name: all_agents_label if name is None else name,
                                      key="overview_agent")
        chosen_threads = [row for row in available_threads
                          if selected_agent is None or reporting_agent_name(row) == selected_agent]
        selected_agents = (frozenset(row["execution_id"] for row in chosen_threads)
                           if selected_chat is not None or selected_agent is not None else None)

    if selected_agents is not None:
        chosen_pairs = {(row["session_id"], row["thread_id"]) for row in chosen_threads}
        selected = selected.loc[[pair in chosen_pairs for pair in zip(selected["session"], selected["agent"])]].copy()
    render_statistics(
        report_calculator, selection, marker, project_keys, selected_agents, bucket
    )
    if selected.empty:
        st.info("No observed events match the selected filters.")
    with st.expander(f"Parsing and usage diagnostics ({len(parsed.diagnostics) + len(usage_diagnostics)})"):
        for item in parsed.diagnostics:
            st.write(f"{item.source}:{item.line or '-'} — {item.message}")
        for item in usage_diagnostics:
            st.write(item["message"])


