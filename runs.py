"""Run definitions and conservative token attribution."""

from dataclasses import dataclass
from datetime import datetime
import math
from uuid import uuid4

from analytics import Increment, Total, aggregate
from parser import Event


def _time(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if result.utcoffset() is not None else None
    except ValueError:
        return None


def validate_run(run):
    """Validate stable run metadata and boundary structure without source access."""
    for key in ("id", "name", "session_id"):
        if not isinstance(run.get(key), str) or not run[key].strip():
            raise ValueError(f"Run {key} must be a non-empty string.")
    for key in ("description", "task_id", "task_type", "execution_mode", "notes"):
        if key in run and run[key] is not None and not isinstance(run[key], str):
            raise ValueError(f"Run {key} must be a string or null.")
    if run.get("outcome", "unknown") not in ("success", "failure", "partial", "unknown"):
        raise ValueError("Run outcome must be success, failure, partial or unknown.")
    score = run.get("evaluation_score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score)):
        raise ValueError("Run evaluation score must be a finite number or null.")
    boundary = run.get("boundary", {"type": "whole_session"})
    if not isinstance(boundary, dict) or boundary.get("type") not in ("whole_session", "timestamps", "events"):
        raise ValueError("Run boundary type must be whole_session, timestamps or events.")
    if boundary["type"] == "timestamps":
        start, end = _time(boundary.get("start")), _time(boundary.get("end"))
        if start is None or end is None or start >= end:
            raise ValueError("Timestamp boundaries require timezone-aware start before end.")
    if boundary["type"] == "events":
        if not all(isinstance(boundary.get(key), str) and boundary[key].strip() for key in ("start_event", "end_event")):
            raise ValueError("Event boundaries require stable start and end event references.")


def upsert_run(data, run):
    """Create or update a run while preserving unrelated annotations."""
    candidate = dict(run)
    candidate.setdefault("id", str(uuid4()))
    validate_run(candidate)
    for index, old in enumerate(data["runs"]):
        if old["id"] == candidate["id"]:
            data["runs"][index] = candidate
            break
    else:
        data["runs"].append(candidate)
    return candidate["id"]


def delete_run(data, run_id):
    """Delete a run and its explicit label assignments."""
    if not any(run["id"] == run_id for run in data["runs"]):
        raise ValueError("Run not found.")
    data["runs"] = [run for run in data["runs"] if run["id"] != run_id]
    data["assignments"] = [item for item in data["assignments"]
                           if not (item["target_type"] == "run" and item["target_id"] == run_id)]


@dataclass(frozen=True)
class RunResult:
    """Run increments, incomplete coverage, and elapsed-time provenance."""

    increments: tuple[Increment, ...]
    totals: dict[str, Total]
    elapsed_seconds: float | None
    elapsed_provenance: str
    attribution: str
    diagnostics: tuple[str, ...]
    event_references: tuple[str, ...]


def calculate_run(run: dict, events: list[Event], increments: list[Increment]) -> RunResult:
    """Attribute root-thread usage to a run, using half-open boundaries.

    Child threads are excluded because their usage overlap is unresolved.
    Event boundaries follow source event order, including equal timestamps.
    Whole-session runs expand as source events and counters are appended.
    """
    validate_run(run)
    session = run["session_id"]
    source_events = [event for event in events if event.session_id == session]
    source_increments = [increment for increment in increments if increment.session_id == session]
    boundary = run.get("boundary", {"type": "whole_session"})
    kind = boundary["type"]
    diagnostics = []
    selected = []
    selected_events = []
    elapsed = None
    provenance = "unknown"
    times = [_time(event.timestamp) for event in source_events]
    observed = [time for time in times if time is not None]
    if "boundaries" in run and "boundary" not in run:
        diagnostics.append("Legacy boundaries are unsupported; choose a supported boundary before calculating usage.")
    elif not source_events:
        diagnostics.append("Source session is unavailable; run usage is unknown.")
    elif kind == "whole_session":
        selected = source_increments
        selected_events = source_events
        if len(observed) >= 2:
            elapsed = (max(observed) - min(observed)).total_seconds()
            provenance = "observed first-to-last activity span; not verified execution duration"
    elif kind == "timestamps":
        start, end = _time(boundary["start"]), _time(boundary["end"])
        if not observed or start < min(observed) or end > max(observed):
            diagnostics.append("Timestamp boundary is outside observed session activity or timestamps are unavailable.")
        else:
            selected = [item for item in source_increments if _time(item.timestamp) is not None and start <= _time(item.timestamp) < end]
            selected_events = [event for event in source_events if _time(event.timestamp) is not None and start <= _time(event.timestamp) < end]
            if any(_time(item.timestamp) is None for item in source_increments):
                diagnostics.append("Untimestamped increments cannot be attributed to the interval.")
            elapsed = (end - start).total_seconds()
            provenance = "manual boundary interval; not verified execution duration"
    else:
        indices = {event.reference: index for index, event in enumerate(source_events)}
        first, last = indices.get(boundary["start_event"]), indices.get(boundary["end_event"])
        if first is None or last is None:
            diagnostics.append("Boundary event is missing from the source session.")
        elif first >= last:
            diagnostics.append("Event boundaries must be in source order with start before end.")
        else:
            selected_events = source_events[first:last]
            refs = {event.reference for event in selected_events}
            selected = [item for item in source_increments if item.reference in refs]
            if any(item.reference not in indices for item in source_increments):
                diagnostics.append("Some increments have no source event and cannot be attributed.")
            if times[first] and times[last] and times[first] <= times[last]:
                elapsed = (times[last] - times[first]).total_seconds()
                provenance = "observed boundary event span; not verified execution duration"
            else:
                diagnostics.append("Boundary event timestamps are missing or out of order; elapsed time is unknown.")
    totals = aggregate(selected)
    if kind != "whole_session" or diagnostics:
        totals = {key: Total(value.value, False) for key, value in totals.items()}
    return RunResult(tuple(selected), totals, elapsed, provenance,
                     "observed counters" if kind == "whole_session" else "estimated from counter observation boundaries",
                     tuple(diagnostics), tuple(event.reference for event in selected_events))


def union_increments(results: list[RunResult]) -> tuple[Increment, ...]:
    """Union overlapping run usage by stable source event reference."""
    unique = {}
    for result in results:
        for increment in result.increments:
            unique.setdefault(increment.reference, increment)
    return tuple(unique.values())


