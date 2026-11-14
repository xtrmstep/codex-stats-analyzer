"""Shared, Streamlit-independent filtering and metrics over token increments."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from internal.analytics.token_accounting import Increment, Total, aggregate
from internal.analytics.agents import analyze_agents
from internal.ingestion.parser import Event
from internal.metadata.labels import assigned, matches


@dataclass(frozen=True)
class Filters:
    """Intersect optional selections; an empty selection matches nothing.

    Dates are inclusive recorded calendar dates. Missing dimensions match only when
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


@dataclass(frozen=True)
class Metrics:
    """Coverage-aware totals and references for one filtered set of increments."""

    totals: dict[str, Total]
    sessions: int
    agents: int
    subagent_share: Total
    references: tuple[str, ...]
    provenance: tuple[str, ...]


_COLUMNS = ("reference", "session", "agent", "parent", "project", "model", "agent_role", "timestamp", "timestamp_text", "increment")



def _recorded_timestamp(value):
    """Parse a timestamp without changing its recorded clock or offset."""
    if value is None:
        return None
    try:
        stamp = pd.Timestamp(value)
        return stamp if not pd.isna(stamp) and stamp.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


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
                     "agent_role": context["agent_role"], "timestamp": event.timestamp, "timestamp_text": event.timestamp,
                     "increment": None})
    for increment in increments:
        context = context_by_reference.get(increment.reference, {})
        rows.append({"reference": increment.reference, "session": increment.session_id,
                     "agent": increment.agent_id, "parent": increment.parent_agent_id,
                     "project": context.get("project"), "model": increment.model,
                     "agent_role": context.get("agent_role"), "timestamp": increment.timestamp, "timestamp_text": increment.timestamp,
                     "increment": increment})
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    frame["timestamp"] = frame["timestamp"].map(_recorded_timestamp)
    return frame


def filter_dataset(frame: pd.DataFrame, selection: Filters, annotations: dict | None = None) -> pd.DataFrame:
    """Apply all selected dimensions and inclusive recorded dates by intersection."""
    if selection.start_date and selection.end_date and selection.start_date > selection.end_date:
        raise ValueError("Start date must not be after end date.")
    mask = pd.Series(True, index=frame.index, dtype=bool)
    for column, selected in (("project", selection.projects), ("model", selection.models),
                             ("session", selection.sessions), ("agent_role", selection.agent_roles)):
        if selected is not None:
            mask &= frame[column].isin(selected)
    dates = frame["timestamp"].map(lambda value: value.date() if value is not None and not pd.isna(value) else None)
    if selection.start_date:
        mask &= dates.map(lambda value: value is not None and value >= selection.start_date)
    if selection.end_date:
        mask &= dates.map(lambda value: value is not None and value <= selection.end_date)
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
    """Group by recorded hour, day, Monday-start week or calendar month."""
    if frequency not in {"hourly", "daily", "weekly", "monthly"}:
        raise ValueError("Unsupported frequency.")
    def bucket(value):
        if value is None or pd.isna(value):
            return None
        local = value.tz_localize(None)
        day = local.normalize()
        if frequency == "hourly":
            return local.floor("h")
        if frequency == "weekly":
            return day - pd.Timedelta(days=day.dayofweek)
        if frequency == "monthly":
            return day.replace(day=1)
        return day
    dated = frame.copy()
    dated["bucket"] = dated["timestamp"].map(bucket)
    return [(None if pd.isna(key) else key, summarize(group, events))
            for key, group in dated.groupby("bucket", dropna=False, sort=True)]
