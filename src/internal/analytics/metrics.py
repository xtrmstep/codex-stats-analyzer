"""Streamlit-independent filtering of observed events."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from internal.ingestion.parser import Event


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


_COLUMNS = ("reference", "session", "agent", "parent", "project", "model", "agent_role", "timestamp", "timestamp_text")


def _recorded_timestamp(value):
    """Parse a timestamp without changing its recorded clock or offset."""
    if value is None:
        return None
    try:
        stamp = pd.Timestamp(value)
        return stamp if not pd.isna(stamp) and stamp.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


def build_dataset(events: list[Event]) -> pd.DataFrame:
    """Attach observed project, role, and model context to each event."""
    contexts: dict[tuple[str, str], dict[str, str | None]] = {}
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
        rows.append({"reference": event.reference, "session": event.session_id,
                     "agent": event.thread_id or event.session_id, "parent": event.parent_agent_id,
                     "project": context["project"], "model": context["model"],
                     "agent_role": context["agent_role"], "timestamp": event.timestamp, "timestamp_text": event.timestamp})
    frame = pd.DataFrame(rows, columns=_COLUMNS)
    frame["timestamp"] = frame["timestamp"].map(_recorded_timestamp)
    return frame


def filter_dataset(frame: pd.DataFrame, selection: Filters) -> pd.DataFrame:
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
    result = frame.loc[mask].copy()
    return result
