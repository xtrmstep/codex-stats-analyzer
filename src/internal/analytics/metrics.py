"""Shared, Streamlit-independent filtering and metrics over token increments."""

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from internal.analytics.token_accounting import Increment, Total, aggregate
from internal.analytics.agents import analyze_agents
from internal.ingestion.parser import Event
from internal.metadata.labels import assigned, matches


@dataclass(frozen=True)
class Filters:
    """Intersect optional selections; an empty selection matches nothing.

    Dates are inclusive UTC calendar dates. Missing dimensions match only when
    no filter for that dimension is selected.
    """

    start_date: date | None = None
    end_date: date | None = None
    projects: frozenset[str] | None = None
    models: frozenset[str] | None = None
    sessions: frozenset[str] | None = None
    agent_roles: frozenset[str] | None = None
    label_ids: frozenset[str] | None = None
    label_mode: str = "all"
    task_types: frozenset[str] | None = None
    execution_modes: frozenset[str] | None = None
    time_zone: str = "UTC"


@dataclass(frozen=True)
class Metrics:
    """Coverage-aware totals and references for one filtered set of increments."""

    totals: dict[str, Total]
    sessions: int
    agents: int
    subagent_share: Total
    references: tuple[str, ...]
    provenance: tuple[str, ...]


_COLUMNS = ("reference", "session", "agent", "parent", "project", "model", "agent_role", "timestamp", "increment")


def build_dataset(events: list[Event], increments: list[Increment]) -> pd.DataFrame:
    """Attach explicitly observed session and agent context to increments.

    Observed event rows retain entities even without counters. Project, role and
    model context carry forward within each session. References keep
    the original accounting event available for provenance. Unknown model
    attribution from accounting is never replaced by contextual model values.
    """
    contexts: dict[tuple[str, str], dict[str, str | None]] = {}
    context_by_reference: dict[str, dict[str, str | None]] = {}
    rows = []
    for event in events:
        owner = (event.session_id, event.thread_id or event.session_id)
        context = contexts.setdefault(owner, {"project": None, "agent_role": None, "model": None})
        if event.project_path:
            context["project"] = event.project_path
        if event.agent_role:
            context["agent_role"] = event.agent_role
        if event.model:
            context["model"] = event.model
        context_by_reference[event.reference] = context.copy()
        rows.append({"reference": event.reference, "session": event.session_id,
                     "agent": event.thread_id or event.session_id, "parent": event.parent_agent_id,
                     "project": context["project"], "model": context["model"],
                     "agent_role": context["agent_role"], "timestamp": event.timestamp,
                     "increment": None})
    for increment in increments:
        context = context_by_reference.get(increment.reference, {})
        rows.append({"reference": increment.reference, "session": increment.session_id,
                     "agent": increment.agent_id, "parent": increment.parent_agent_id,
                     "project": context.get("project"), "model": increment.model,
                     "agent_role": context.get("agent_role"), "timestamp": increment.timestamp,
                     "increment": increment})
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], format="mixed", utc=True, errors="coerce")
    return frame


def filter_dataset(frame: pd.DataFrame, selection: Filters, annotations: dict | None = None) -> pd.DataFrame:
    """Apply all selected dimensions and inclusive UTC dates by intersection."""
    if selection.start_date and selection.end_date and selection.start_date > selection.end_date:
        raise ValueError("Start date must not be after end date.")
    mask = pd.Series(True, index=frame.index, dtype=bool)
    for column, selected in (("project", selection.projects), ("model", selection.models),
                             ("session", selection.sessions), ("agent_role", selection.agent_roles)):
        if selected is not None:
            mask &= frame[column].isin(selected)
    if selection.start_date:
        mask &= frame["timestamp"] >= pd.Timestamp(selection.start_date, tz=selection.time_zone).tz_convert("UTC")
    if selection.end_date:
        mask &= frame["timestamp"] < pd.Timestamp(selection.end_date + timedelta(days=1), tz=selection.time_zone).tz_convert("UTC")
    manual = any(value is not None for value in (selection.label_ids, selection.task_types, selection.execution_modes))
    if manual:
        if annotations is None:
            raise ValueError("Manual filters require loaded annotations.")
        sessions = {session for session in frame["session"].dropna().unique()
                    if matches(annotations, assigned(annotations, "session", session), selection.label_ids,
                               selection.label_mode, selection.task_types, selection.execution_modes)}
        mask &= frame["session"].isin(sessions)
    result = frame.loc[mask].copy()
    result.attrs["manual_filter"] = manual
    return result


def _overlapping_streams(frame: pd.DataFrame, events: list[Event]) -> bool:
    """Identify known ancestor relationships even through filtered-out agents."""
    streams = set(frame["session"].dropna())
    if len(streams) < 2:
        return False
    analysis = analyze_agents(next(iter(streams)), events, [])
    for stream in streams:
        agent = analysis.agents.get(stream)
        ancestor = agent.parent_id if agent else None
        visited = {stream}
        while ancestor and ancestor not in visited:
            if ancestor in streams:
                return True
            visited.add(ancestor)
            parent = analysis.agents.get(ancestor)
            ancestor = parent.parent_id if parent else None
    return False


def summarize(frame: pd.DataFrame, events: list[Event]) -> Metrics:
    """Aggregate once for every view; withhold related streams with unknown overlap."""
    increments = [increment for increment in frame["increment"] if increment is not None]
    totals = aggregate(increments)
    usage_frame = frame.loc[frame["increment"].notna()]
    if _overlapping_streams(usage_frame, events):
        totals = {name: Total(None, False) for name in totals}
    elif set(frame["session"].dropna()) - set(usage_frame["session"].dropna()):
        totals = {name: Total(total.value, False) for name, total in totals.items()}
    if frame.attrs.get("run_filter"):
        totals = {name: Total(total.value, False) for name, total in totals.items()}
    refs = tuple(dict.fromkeys(frame["reference"].tolist()))
    manual_provenance = ("manual classification filters",) if frame.attrs.get("manual_filter") else ()
    return Metrics(totals, frame["session"].nunique(), frame["agent"].nunique(),
                   Total(None, False), refs,
                   (("observed events", "observed counters", "estimated timing within counter intervals")
                    if increments else ("observed events",) if not frame.empty else ()) + manual_provenance)


def grouped(frame: pd.DataFrame, events: list[Event], dimension: str) -> list[tuple[object, Metrics]]:
    """Group by project, model or session, retaining an explicit unknown group."""
    if dimension not in {"project", "model", "session"}:
        raise ValueError("Grouping dimension must be project, model or session.")
    return [(None if pd.isna(key) else key, summarize(group, events))
            for key, group in frame.groupby(dimension, dropna=False, sort=False)]


def time_buckets(frame: pd.DataFrame, events: list[Event], frequency: str) -> list[tuple[pd.Timestamp | None, Metrics]]:
    """Group by UTC day, Monday-start week, or calendar month; keep unknown dates."""
    if frequency not in {"daily", "weekly", "monthly"}:
        raise ValueError("Frequency must be daily, weekly or monthly.")
    dated = frame.copy()
    day = dated["timestamp"].dt.floor("D")
    if frequency == "daily":
        dated["bucket"] = day
    elif frequency == "weekly":
        dated["bucket"] = day - pd.to_timedelta(day.dt.dayofweek, unit="D")
    else:
        dated["bucket"] = pd.to_datetime(day.dt.strftime("%Y-%m-01"), utc=True, errors="coerce")
    return [(None if pd.isna(key) else key, summarize(group, events))
            for key, group in dated.groupby("bucket", dropna=False, sort=True)]






