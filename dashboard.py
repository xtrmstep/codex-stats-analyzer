"""Streamlit dashboard using the shared analytics contract."""

from pathlib import Path
from dataclasses import replace

import pandas as pd
import plotly.express as px
import streamlit as st

from agents import analyze_agents
from analytics import calculate_increments
from metrics import Filters, build_dataset, filter_dataset, grouped, summarize, time_buckets
from parser import ingest
from annotations import MetadataStore, StorageError, missing_sessions
from labels_ui import manage
from labels import assigned, matches, run_labels
from run_ui import manage_runs, select_runs, run_summary
from experiment_ui import render_experiments
from exports import csv_bytes, SESSION_COLUMNS, RUN_COLUMNS
from refresh import source_manifest, changes
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


def _chart_rows(groups):
    return [{"Group": str(key) if key is not None else "Unknown", "Tokens": metric.totals["total_tokens"].value,
             "Coverage": "Complete" if metric.totals["total_tokens"].complete else "Partial or unknown"}
            for key, metric in groups]


def render(sources):
    """Render the overview and selected session from local read-only sources."""
    refresh_requested = st.sidebar.button("Refresh sources")
    manifest_key = "source_manifest"
    if refresh_requested or manifest_key not in st.session_state:
        manifest, fingerprint_diagnostics = source_manifest(sources)
        previous = st.session_state.get(manifest_key)
        if refresh_requested and previous is not None:
            st.session_state["source_changes"] = changes(previous, manifest)
        st.session_state[manifest_key] = manifest
        st.session_state["fingerprint_diagnostics"] = fingerprint_diagnostics
    parsed = ingest(sources)
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
    if refresh_requested:
        report = st.session_state.get("source_changes", {"new": [], "changed": [], "missing": []})
        st.info(f"Refresh: {len(report['new'])} new, {len(report['changed'])} changed, {len(report['missing'])} unavailable or moved source files. All analytics and saved comparisons are recalculated.")
        with st.expander("Source changes"):
            for kind, paths in report.items():
                for path in paths:
                    st.write(f"{kind}: {path}")
        for diagnostic in st.session_state.get("fingerprint_diagnostics", []):
            st.warning(str(diagnostic))
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
    st.sidebar.caption("Manual filters select matching session usage and matching run intervals. Run boundaries are estimated; overlapping runs are counted once globally.")
    use_dates = st.sidebar.checkbox("Filter dates (UTC)")
    start = end = None
    if use_dates:
        dates = frame["timestamp"].dropna()
        if dates.empty:
            st.sidebar.info("No timestamped events are available.")
        else:
            bounds = st.sidebar.date_input("UTC date range", (dates.min().date(), dates.max().date()))
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
    selection = Filters(start_date=start, end_date=end,
                        label_ids=frozenset(chosen_labels) if chosen_labels else None, label_mode=label_mode,
                        task_types=frozenset(task_types) if task_types else None,
                        execution_modes=frozenset(execution_modes) if execution_modes else None,
                        projects=_options(frame, "project", "Projects"),
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
    metrics = summarize(selected, parsed.events)
    st.caption("UTC dates filter observed event times. Usage may have occurred before its counter timestamp. Partial totals are not complete coverage.")
    columns = st.columns(5)
    columns[0].metric("Total tokens", _display(metrics.totals["total_tokens"]))
    columns[1].metric("Input tokens", _display(metrics.totals["input_tokens"]))
    columns[2].metric("Output tokens", _display(metrics.totals["output_tokens"]))
    columns[3].metric("Cache percentage", _display(metrics.totals["cache_percentage"], "%"))
    columns[4].metric("Sessions / agents", f"{metrics.sessions} / {metrics.agents}")
    st.caption(f"Subagent share: {_display(metrics.subagent_share, '%')}. Parent counters may include child usage.")
    run_rows, run_mean, run_median = run_summary(run_matches, parsed.events, snapshot.data if snapshot else None)
    run_columns = st.columns(3)
    run_columns[0].metric("Runs", len(run_rows))
    run_columns[1].metric("Average tokens per run", f"{run_mean:,.1f} (known only)" if run_mean is not None else "Unknown")
    run_columns[2].metric("Median tokens per run", f"{run_median:,.1f} (known only)" if run_median is not None else "Unknown")
    st.caption("Run totals cover root-thread counters only, may be partial, and exclude child usage. Overlapping runs and multiple labels are not additive.")
    if selected.empty:
        st.info("No observed events match the selected filters.")
    else:
        frequency = st.radio("Time aggregation", ["daily", "weekly", "monthly"], horizontal=True)
        trend = pd.DataFrame(_chart_rows(time_buckets(selected, parsed.events, frequency)))
        st.subheader("Token usage over time")
        if trend["Tokens"].notna().any():
            st.plotly_chart(px.bar(trend, x="Group", y="Tokens", color="Coverage", labels={"Group": "UTC period"}), use_container_width=True)
        else:
            st.info("Token usage is unknown for these periods.")
        st.caption("Unknown dates form a separate group. Group totals may overlap and should not be added.")
        dimension = st.selectbox("Break down by", ["project", "model", "session", "run", "label"])
        if dimension in {"run", "label"}:
            breakdown_rows = []
            category_indices = {}
            for run, result, run_frame in run_matches:
                if dimension == "run":
                    value = summarize(run_frame, parsed.events).totals["total_tokens"]
                    breakdown_rows.append({"Group": run["name"], "Tokens": value.value, "Coverage": "Partial or unknown"})
                else:
                    explicit, inherited = run_labels(snapshot.data, run)
                    names = [definitions[label]["name"] for label in explicit | inherited if label in definitions] or ["Unlabeled"]
                    for name in names:
                        category_indices.setdefault(name, set()).update(run_frame.index)
            if dimension == "label":
                for session in selected["session"].dropna().unique():
                    for label in assigned(snapshot.data, "session", session):
                        if label in definitions:
                            category_indices.setdefault(definitions[label]["name"], set()).update(selected.index[selected["session"] == session])
                for name, indices in category_indices.items():
                    subset = selected.loc[selected.index.isin(indices)].copy()
                    subset.attrs["run_filter"] = True
                    value = summarize(subset, parsed.events).totals["total_tokens"]
                    breakdown_rows.append({"Group": name, "Tokens": value.value, "Coverage": "Partial or unknown"})
            breakdown = pd.DataFrame(breakdown_rows, columns=["Group", "Tokens", "Coverage"])
        else:
            breakdown = pd.DataFrame(_chart_rows(grouped(selected, parsed.events, dimension)))
        st.subheader("Token breakdown")
        if breakdown["Tokens"].notna().any():
            st.plotly_chart(px.bar(breakdown, x="Group", y="Tokens", color="Coverage"), use_container_width=True)
        else:
            st.info("No known token totals for this breakdown.")
        st.subheader("Input and output")
        distribution = [{"Component": label, "Tokens": metrics.totals[key].value, "Coverage": "Complete" if metrics.totals[key].complete else "Partial or unknown"}
                        for label, key in (("Cached input", "cached_input_tokens"), ("Non-cached input", "non_cached_input_tokens"), ("Output", "output_tokens"))]
        if any(item["Tokens"] is not None for item in distribution):
            st.plotly_chart(px.bar(pd.DataFrame(distribution), x="Component", y="Tokens", color="Coverage"), use_container_width=True)
        else:
            st.info("Token components are unknown.")
        st.subheader("Runs")
        st.dataframe(pd.DataFrame(run_rows), hide_index=True, use_container_width=True)
        st.download_button("Download filtered runs CSV", csv_bytes(run_rows, RUN_COLUMNS), file_name="runs.csv", mime="text/csv")
        st.subheader("Sessions")
        sessions = grouped(selected, parsed.events, "session")
        session_rows = []
        for key, value in sessions:
            times = selected.loc[selected["session"] == key, "timestamp"].dropna()
            session_rows.append({"Session": key, "Tokens": value.totals["total_tokens"].value,
                                 "Input": value.totals["input_tokens"].value, "Output": value.totals["output_tokens"].value,
                                 "Coverage": "Complete" if value.totals["total_tokens"].complete else "Partial or unknown",
                                 "Provenance": "; ".join(value.provenance),
                                 "Agents": value.agents,
                                 "First observed UTC": times.min().isoformat() if not times.empty else None,
                                 "Last observed UTC": times.max().isoformat() if not times.empty else None})
        st.dataframe(pd.DataFrame(session_rows), hide_index=True, use_container_width=True)
        st.download_button("Download filtered sessions CSV", csv_bytes(session_rows, SESSION_COLUMNS), file_name="sessions.csv", mime="text/csv")
        st.caption("CSV uses UTF-8 with BOM, UTC ISO 8601 timestamps, blank unknown values and token/second units indicated in the column names.")
        session_ids = sorted(selected["session"].dropna().unique().tolist())
        if session_ids:
            root = st.selectbox("Session detail", session_ids)
            details(root, selected, parsed.events, accounting.increments, use_dates)
    if snapshot is not None:
        render_experiments(snapshot.data, parsed.events, accounting.increments, selected, selection, selected_agent, chosen_runs)
    with st.expander(f"Parsing and accounting diagnostics ({len(parsed.diagnostics) + len(accounting.diagnostics)})"):
        for item in parsed.diagnostics:
            st.write(f"{item.source}:{item.line or '-'} — {item.message}")
        for item in accounting.diagnostics:
            st.write(item)


def details(root, selected, events, increments, date_filter_active=False):
    """Show hierarchy as context, while all usage follows active filters."""
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
        agent_frame = selected.loc[selected["agent"] == agent_id]
        totals = summarize(agent_frame, events)
        rows.append({"Agent": agent_id, "Parent": agent.parent_id, "Role": agent.role, "Nickname": agent.nickname,
                     "Model": agent.model, "Status": agent.status, "Tokens": _display(totals.totals["total_tokens"]),
                     "Cache %": _display(totals.totals["cache_percentage"], "%"),
                     "First observed": agent.activity.first, "Last observed": agent.activity.last})
        activity = agent.activity
        times = pd.to_datetime(
            [event.timestamp for event in events if event.session_id == agent_id
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
    st.write(f"Main agent tokens under filters: {_display(summarize(selected.loc[selected['agent'] == root], events).totals['total_tokens'])}")
    descendant_ids = tree_ids - {root}
    main_metrics = summarize(selected.loc[selected["agent"] == root], events)
    sub_metrics = summarize(selected.loc[selected["agent"].isin(descendant_ids)], events)
    comparison = [{"Agent group": label, "Tokens": item.totals["total_tokens"].value,
                   "Coverage": "Complete" if item.totals["total_tokens"].complete else "Partial or unknown"}
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













