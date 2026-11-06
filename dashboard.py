"""Streamlit dashboard using the shared analytics contract."""

import pandas as pd
import plotly.express as px
import streamlit as st

from agents import analyze_agents
from analytics import calculate_increments
from metrics import Filters, build_dataset, filter_dataset, grouped, summarize, time_buckets
from parser import ingest


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
    parsed = ingest(sources)
    accounting = calculate_increments(parsed.events)
    frame = build_dataset(parsed.events, accounting.increments)
    st.sidebar.header("Filters")
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
    selection = Filters(start_date=start, end_date=end,
                        projects=_options(frame, "project", "Projects"),
                        models=_options(frame, "model", "Models"),
                        sessions=_options(frame, "session", "Sessions"),
                        agent_roles=_options(frame, "agent_role", "Agent roles"))
    selected = filter_dataset(frame, selection)
    available_agents = sorted(selected["agent"].dropna().unique().tolist())
    selected_agent = st.sidebar.selectbox("Agent", ["All agents"] + available_agents)
    if selected_agent != "All agents":
        selected = selected.loc[selected["agent"] == selected_agent].copy()
    metrics = summarize(selected, parsed.events)
    st.caption("UTC dates filter observed event times. Usage may have occurred before its counter timestamp. Partial totals are not complete coverage.")
    columns = st.columns(5)
    columns[0].metric("Total tokens", _display(metrics.totals["total_tokens"]))
    columns[1].metric("Input tokens", _display(metrics.totals["input_tokens"]))
    columns[2].metric("Output tokens", _display(metrics.totals["output_tokens"]))
    columns[3].metric("Cache percentage", _display(metrics.totals["cache_percentage"], "%"))
    columns[4].metric("Sessions / agents", f"{metrics.sessions} / {metrics.agents}")
    st.caption(f"Subagent share: {_display(metrics.subagent_share, '%')}. Parent counters may include child usage.")
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
        dimension = st.selectbox("Break down by", ["project", "model", "session"])
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
        st.subheader("Sessions")
        sessions = grouped(selected, parsed.events, "session")
        st.dataframe(pd.DataFrame([{"Session": key, "Tokens": value.totals["total_tokens"].value,
                                    "Input": value.totals["input_tokens"].value, "Output": value.totals["output_tokens"].value,
                                    "Coverage": "Complete" if value.totals["total_tokens"].complete else "Partial or unknown",
                                    "Agents": value.agents} for key, value in sessions]), hide_index=True, use_container_width=True)
        session_ids = sorted(selected["session"].dropna().unique().tolist())
        if session_ids:
            root = st.selectbox("Session detail", session_ids)
            details(root, selected, parsed.events, accounting.increments, use_dates)
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




