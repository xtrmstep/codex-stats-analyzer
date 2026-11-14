"""Coverage-aware reporting over one committed SQLite snapshot."""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import sqlite3
from uuid import uuid4

import pandas as pd
from collection import CodexLogReader
from parser import parse_collected
from transformations import _project


TOKEN_FIELDS = ("total_tokens", "input_tokens", "output_tokens", "cached_input_tokens",
                "non_cached_input_tokens", "cache_write_input_tokens", "reasoning_output_tokens")


@dataclass(frozen=True)
class TimeMarker:
    """A named UTC timestamp retained across imports and restarts."""

    marker_id: str
    name: str
    timestamp: str


@dataclass(frozen=True)
class StatsRequest:
    """Filters and time windows for a single report."""

    start: pd.Timestamp | None = None
    end: pd.Timestamp | None = None
    time_zone: str = "UTC"
    bucket: str = "daily"
    agent_grouping: str = "thread"
    marker: TimeMarker | None = None
    projects: frozenset[str] | None = None
    models: frozenset[str] | None = None
    sessions: frozenset[str] | None = None
    roles: frozenset[str] | None = None
    agents: frozenset[str] | None = None
    record_ids: frozenset[str] | None = None
    resolved_start: pd.Timestamp | None = None
    resolved_end: pd.Timestamp | None = None


@dataclass(frozen=True)
class UsageMeasurement:
    """One report window or grouped result with its known coverage."""

    scope: str
    start: pd.Timestamp | None
    end: pd.Timestamp | None
    project: str | None
    agent: str | None
    bucket: pd.Timestamp | None
    totals: dict[str, int | None]
    coverage: str
    cache_percentage: float | None
    average_daily_tokens: float | None
    sessions: int
    agents: int
    subagent_share: float | None = None
    empty_window: bool = False


def list_markers(connection: sqlite3.Connection) -> list[TimeMarker]:
    """Read saved markers in name order."""
    return [TimeMarker(*row) for row in connection.execute(
        "SELECT marker_id, name, timestamp FROM time_markers ORDER BY name COLLATE NOCASE, marker_id"
    )]


def save_marker(writer, name: str, timestamp: str, marker_id: str | None = None) -> TimeMarker:
    """Create or edit one marker using the generic writer transaction."""
    name = name.strip()
    if not name:
        raise ValueError("Marker name is required.")
    stamp = pd.Timestamp(timestamp)
    if pd.isna(stamp) or stamp.tzinfo is None:
        raise ValueError("Marker timestamp must include a time zone.")
    marker = TimeMarker(marker_id or str(uuid4()), name, stamp.tz_convert("UTC").isoformat())
    if marker_id and not writer.connection.execute(
        "SELECT 1 FROM time_markers WHERE marker_id = ?", (marker_id,)
    ).fetchone():
        raise ValueError("Marker no longer exists.")
    with writer.transaction():
        writer.write("time_markers", {"marker_id": "marker_id", "name": "name", "timestamp": "timestamp"},
                     [vars(marker)], ("marker_id",))
    return marker


def delete_marker(writer, marker_id: str) -> None:
    """Delete a saved marker atomically."""
    with writer.transaction():
        cursor = writer.connection.execute("DELETE FROM time_markers WHERE marker_id = ?", (marker_id,))
        if not cursor.rowcount:
            raise ValueError("Marker no longer exists.")


def _timestamp(value):
    if value is None:
        return None
    stamp = pd.Timestamp(value)
    if pd.isna(stamp) or stamp.tzinfo is None:
        raise ValueError("Report timestamps must have a time zone.")
    return stamp.tz_convert("UTC")


def _agent(row, grouping):
    if grouping == "thread":
        return row["thread_id"]
    if grouping == "name":
        return row["agent_name"] or row["role"]
    raise ValueError("Agent grouping must be thread or name.")


def _bucket(value, request):
    if value is None:
        return None
    local = value.tz_convert(request.time_zone)
    if request.bucket == "hourly":
        return local.floor("h", ambiguous=False, nonexistent="shift_forward")
    day = local.normalize()
    if request.bucket == "daily":
        return day
    if request.bucket == "weekly":
        return day - pd.DateOffset(days=day.dayofweek)
    if request.bucket == "monthly":
        return day.replace(day=1)
    raise ValueError("Unsupported time bucket.")


def _measure(rows, scope, start, end, project=None, agent=None, bucket=None, diagnostics=(), empty=False):
    if empty:
        return UsageMeasurement(scope, start, end, project, agent, bucket,
                                {field: None for field in TOKEN_FIELDS}, "unknown", None, None, 0, 0, empty_window=True)
    totals = {}
    executions = {row["execution_id"] for row in rows if row["execution_id"]}
    relevant_diagnostics = []
    for item in diagnostics:
        if item.get("kind", "usage") != "usage":
            continue
        if item.get("execution_id") is not None and item["execution_id"] not in executions:
            continue
        observed = _timestamp(item.get("observed_at"))
        if observed is not None and ((start is not None and observed < start) or (end is not None and observed >= end)):
            continue
        relevant_diagnostics.append(item)
    complete = bool(rows) and not relevant_diagnostics
    for field in TOKEN_FIELDS:
        known = [row[field] for row in rows if row[field] is not None]
        totals[field] = sum(known) if known else None
        if field in ("total_tokens", "input_tokens", "output_tokens") and len(known) != len(rows):
            complete = False
    eligible = [row for row in rows if row["input_tokens"] is not None and row["cached_input_tokens"] is not None]
    if len(eligible) != len(rows):
        complete = False
    input_total = sum(row["input_tokens"] for row in eligible)
    cached_total = sum(row["cached_input_tokens"] for row in eligible)
    cache = 100 * cached_total / input_total if input_total else None
    if any(row["coverage"] != "complete" or row["uncertain"] for row in rows):
        complete = False
    coverage = "complete" if complete else "partial" if totals["total_tokens"] is not None else "unknown"
    hierarchy_uncertain = any(item.get("kind") == "hierarchy" for item in diagnostics)
    independently_counted = all(row["counter_provenance"] == "response" for row in rows)
    share = None
    if complete and not hierarchy_uncertain and independently_counted and totals["total_tokens"]:
        subagent_total = sum(row["total_tokens"] for row in rows if row["parent_execution_id"] is not None)
        share = 100 * subagent_total / totals["total_tokens"]
    days = (end - start).total_seconds() / 86400 if start is not None and end is not None else 0
    daily = totals["total_tokens"] / days if totals["total_tokens"] is not None and days > 0 else None
    return UsageMeasurement(scope, start, end, project, agent, bucket, totals, coverage, cache, daily,
                            len({row["session_id"] for row in rows if row["session_id"]}),
                            len({row["execution_id"] for row in rows if row["execution_id"]}), share)


class UsageCalculator:
    """Group report rows using the same measurement logic as the summary."""

    def groups(self, rows, request, scope, start, end, diagnostics):
        """Return grouped measurements for one resolved window."""
        grouped = {}
        for row in rows:
            key = self.key(row, request)
            grouped.setdefault(key, []).append(row)
        results = []
        for (project, agent, bucket), group in grouped.items():
            group_start, group_end = start, end
            if bucket is not None:
                bucket_start = bucket.tz_convert("UTC")
                if request.bucket == "hourly":
                    bucket_end = bucket_start + pd.Timedelta(hours=1)
                elif request.bucket == "daily":
                    bucket_end = (bucket + pd.DateOffset(days=1)).tz_convert("UTC")
                elif request.bucket == "weekly":
                    bucket_end = (bucket + pd.DateOffset(days=7)).tz_convert("UTC")
                else:
                    bucket_end = (bucket + pd.DateOffset(months=1)).tz_convert("UTC")
                group_start = max(start, bucket_start) if start is not None else bucket_start
                group_end = min(end, bucket_end) if end is not None else bucket_end
            if bucket is not None:
                group = [{**row, "uncertain": row["uncertain"] or (
                    row["counter_provenance"] == "legacy_delta" and group_start is not None
                    and (row["prior"] is None or row["prior"] < group_start)
                )} for row in group]
            results.append(_measure(group, scope, group_start, group_end, project, agent, bucket, diagnostics))
        return results


class ProjectUsageOverTimeCalculator(UsageCalculator):
    """Group usage by project and time."""

    def key(self, row, request):
        return row["project_key"], None, _bucket(row["observed"], request)


class AgentUsageOverTimeCalculator(UsageCalculator):
    """Group usage by agent and time."""

    def key(self, row, request):
        return None, _agent(row, request.agent_grouping), _bucket(row["observed"], request)


class AgentUsageByProjectCalculator(UsageCalculator):
    """Group usage by agent and project."""

    def key(self, row, request):
        return row["project_key"], _agent(row, request.agent_grouping), None


class ModelUsageCalculator(UsageCalculator):
    """Group usage by model."""

    def key(self, row, request):
        return None, row["model"], None


class SessionUsageCalculator(UsageCalculator):
    """Group usage by session."""

    def key(self, row, request):
        return None, row["session_id"], None


class StatsCalculation:
    """Resolve report windows from a single committed database snapshot."""

    def __init__(self, database_path):
        self.database_path = str(database_path)
        self.report_time = pd.Timestamp(datetime.now(timezone.utc))
        self.calculators = {
            "Project over time": ProjectUsageOverTimeCalculator(),
            "Agent over time": AgentUsageOverTimeCalculator(),
            "Agent by project": AgentUsageByProjectCalculator(),
            "Model": ModelUsageCalculator(),
            "Session": SessionUsageCalculator(),
        }
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("BEGIN")
            state = connection.execute("SELECT initialized FROM import_state WHERE id = 1").fetchone()
            if not state or not state["initialized"]:
                raise ValueError("No successful usage publication is available.")
            self.rows = [dict(row) for row in connection.execute(
                "SELECT u.*, t.session_id, t.thread_id, t.agent_name, t.role, t.nickname, t.parent_execution_id "
                "FROM usage_records u LEFT JOIN agent_threads t ON t.execution_id = u.execution_id"
            )]
            self.diagnostics = [dict(row) for row in connection.execute("SELECT * FROM coverage_diagnostics")]
            self.threads = [dict(row) for row in connection.execute("SELECT * FROM agent_threads")]
            self.parents = {row["execution_id"]: row["parent_execution_id"] for row in self.threads}
            records = CodexLogReader().replay_publication(connection)
            connection.commit()
        finally:
            connection.close()
        self.parsed = parse_collected(records)
        self.events = self.parsed.events

    def calculate(self, request: StatsRequest):
        """Return summary and grouped measurements for each requested scope."""
        rows = [row.copy() for row in self.rows]
        diagnostics = self.diagnostics
        parents = self.parents
        start, end = _timestamp(request.start), _timestamp(request.end)
        if start is not None and end is not None and start >= end:
            raise ValueError("The reporting end must be after the start.")
        selected = []
        for row in rows:
            if any(choices is not None and row[field] not in choices for field, choices in
                   (("project_key", request.projects), ("model", request.models), ("session_id", request.sessions),
                    ("role", request.roles), ("thread_id", request.agents), ("source_record_id", request.record_ids))):
                continue
            row["observed"] = _timestamp(row["observed_at"])
            row["prior"] = _timestamp(row["prior_observed_at"])
            selected.append(row)
        thread_lookup = {(thread["session_id"], thread["thread_id"]): thread for thread in self.threads}
        observations = []
        for event in self.events:
            thread = thread_lookup.get((event.session_id, event.thread_id))
            if thread is None:
                continue
            project, _ = _project(event.project_path, event.repository_url)
            if any(choices is not None and value not in choices for value, choices in
                   ((project, request.projects), (event.model, request.models), (event.session_id, request.sessions),
                    (thread["role"], request.roles), (event.thread_id, request.agents), (event.record_id, request.record_ids))):
                continue
            try:
                stamp = _timestamp(event.timestamp) if event.timestamp else None
            except (TypeError, ValueError, OverflowError):
                stamp = None
            observations.append((event.session_id, thread["execution_id"], stamp))
        observed = ([row["observed"] for row in selected if row["observed"] is not None]
                    + [stamp for _, _, stamp in observations if stamp is not None])
        effective_start = start if start is not None else (_timestamp(request.resolved_start) or min(observed, default=None))
        effective_end = end if end is not None else (_timestamp(request.resolved_end) or max(
            self.report_time, max(observed) + pd.Timedelta(nanoseconds=1) if observed else self.report_time
        ))
        scopes = [("Full selected period", start, effective_start)]
        if request.marker:
            marker = _timestamp(request.marker.timestamp)
            cutoff = max(effective_start, marker) if effective_start is not None else marker
            scopes.append((f"Since {request.marker.name}", cutoff, cutoff))
        result = {}
        for scope, cutoff, display_start in scopes:
            empty = cutoff is not None and cutoff >= effective_end
            window = []
            for original in selected:
                row = original.copy()
                observed_at = row["observed"]
                if (cutoff is not None and (observed_at is None or observed_at < cutoff)) or (end is not None and (observed_at is None or observed_at >= end)):
                    continue
                row["uncertain"] = bool(row["counter_provenance"] == "legacy_delta" and cutoff is not None
                                        and (row["prior"] is None or row["prior"] < cutoff))
                window.append(row)
            included = {row["execution_id"] for row in window if row["execution_id"]}
            overlapping = set()
            for execution_id in included:
                ancestor = parents.get(execution_id)
                seen = {execution_id}
                while ancestor and ancestor not in seen:
                    if ancestor in included:
                        overlapping.add(ancestor)
                    seen.add(ancestor)
                    ancestor = parents.get(ancestor)
            excluded = [row for row in window if row["execution_id"] in overlapping
                        and row["counter_provenance"] == "legacy_delta"]
            if excluded:
                window = [row for row in window if row not in excluded]
            scoped_diagnostics = diagnostics + ([{"message": "Overlapping legacy agent counters withheld."}] if excluded else [])
            summary = _measure(window, scope, display_start, effective_end, diagnostics=scoped_diagnostics, empty=empty)
            if not empty:
                observed_sessions = {row["session_id"] for row in window if row["session_id"]}
                observed_agents = {row["execution_id"] for row in window if row["execution_id"]}
                for session_id, execution_id, stamp in observations:
                    if (cutoff is not None and (stamp is None or stamp < cutoff)) or (end is not None and (stamp is None or stamp >= end)):
                        continue
                    observed_sessions.add(session_id)
                    observed_agents.add(execution_id)
                summary = replace(summary, sessions=len(observed_sessions), agents=len(observed_agents))
            groups = {name: calculator.groups(window, request, scope, display_start, effective_end, scoped_diagnostics)
                      for name, calculator in self.calculators.items()}
            result[scope] = (summary, groups)
        return result
