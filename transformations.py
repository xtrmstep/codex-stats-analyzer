"""Transform collected Codex records into attributable threads and usage."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import re

from analytics import calculate_increments, calculate_response_usage
from agents import analyze_agents
from parser import parse_collected


@dataclass(frozen=True)
class CodexAgentThread:
    """A verified execution identity and its available agent metadata."""

    execution_id: str
    session_id: str
    thread_id: str
    parent_execution_id: str | None
    agent_name: str | None
    role: str | None
    nickname: str | None


@dataclass(frozen=True)
class CodexUsage:
    """A response or counter delta tied to its collected evidence."""

    usage_id: str
    source_record_id: str
    execution_id: str | None
    observed_at: str | None
    prior_observed_at: str | None
    source_working_directory: str | None
    project_key: str | None
    project_label: str | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    cached_input_tokens: int | None
    cache_write_input_tokens: int | None
    reasoning_output_tokens: int | None
    total_tokens: int | None
    non_cached_input_tokens: int | None
    coverage: str
    counter_provenance: str


class CodexRecordTransformation(ABC):
    """Describe a destination and derive rows from a raw snapshot."""

    @property
    @abstractmethod
    def record_type(self):
        """Return the dataclass produced by this transformation."""

    @property
    @abstractmethod
    def destination(self):
        """Return the SQLite table and destination-to-source mapping."""

    @abstractmethod
    def transform(self, records):
        """Return derived rows and coverage diagnostics for a snapshot."""


def _execution_id(session: str, thread: str) -> str:
    return hashlib.sha256(json.dumps([session, thread]).encode("utf-8")).hexdigest()


def _utc(value: str | None) -> str | None:
    if not value:
        return None
    match = re.fullmatch(r"(\d{4}-\d\d-\d\d[Tt ]\d\d:\d\d:\d\d)(\.\d+)?([Zz]|[+-]\d\d:\d\d)", value)
    if not match:
        return None
    try:
        base = datetime.fromisoformat(match.group(1) + match.group(3).upper().replace("Z", "+00:00"))
        return base.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + (match.group(2) or "") + "Z"
    except ValueError:
        return None


def _events(records):
    parsed = parse_collected(records)
    by_position = {}
    by_record = {event.record_id: event for event in parsed.events}
    record_logs = {record.record_id: record.log_identity for record in records}
    owners_by_log = {}
    for event in parsed.events:
        if event.thread_id:
            owners_by_log.setdefault(record_logs[event.record_id], set()).add(
                _execution_id(event.session_id, event.thread_id)
            )
    for record in records:
        by_position.setdefault((record.source_path, record.line_number), []).append(record.record_id)
    diagnostics = []
    for item in parsed.diagnostics:
        candidates = by_position.get((item.source, item.line), [])
        record_id = candidates[0] if len(candidates) == 1 else None
        event = by_record.get(record_id)
        execution_id = _execution_id(event.session_id, event.thread_id) if event and event.thread_id else None
        if event is None and record_id:
            owners = owners_by_log.get(record_logs[record_id], set())
            execution_id = next(iter(owners)) if len(owners) == 1 else None
        diagnostics.append({"source_record_id": record_id, "execution_id": execution_id,
                            "observed_at": _utc(event.timestamp) if event else None,
                            "message": f"{item.source}:{item.line or '-'}: {item.message}"})
    return parsed.events, diagnostics


def _threads(events):
    data = {}
    parents = {}
    sessions_by_thread = {}
    for event in events:
        if event.thread_id:
            sessions_by_thread.setdefault(event.thread_id, set()).add(event.session_id)
    for event in events:
        if not event.thread_id or len(sessions_by_thread[event.thread_id]) != 1:
            continue
        execution_id = _execution_id(event.session_id, event.thread_id)
        item = data.setdefault(execution_id, {"execution_id": execution_id, "session_id": event.session_id,
                                              "thread_id": event.thread_id, "parent_execution_id": None,
                                              "agent_name": None, "role": None, "nickname": None})
        if event.agent_role:
            item["role"] = event.agent_role
            item["agent_name"] = event.agent_role
        if event.agent_nickname:
            item["nickname"] = event.agent_nickname
        if event.parent_agent_id:
            parents.setdefault(execution_id, set()).add(event.parent_agent_id)
        evidence = event.evidence or {}
        if evidence.get("type") == "collab_agent_spawn":
            sender, receiver = evidence.get("sender_thread_id"), evidence.get("receiver_thread_id")
            if sender and receiver:
                parents.setdefault(("thread", receiver), set()).add(sender)
    by_thread = {}
    for item in data.values():
        by_thread.setdefault(item["thread_id"], []).append(item["execution_id"])
    if data:
        root_thread = next(iter(data.values()))["thread_id"]
        analysis = analyze_agents(root_thread, [event for event in events if event.thread_id], [])
        for thread_id, agent in analysis.agents.items():
            if agent.parent_id:
                parents.setdefault(("thread", thread_id), set()).add(agent.parent_id)
    for execution_id, item in data.items():
        candidates = parents.get(execution_id, set()) | parents.get(("thread", item["thread_id"]), set())
        if len(candidates) == 1:
            matches = by_thread.get(next(iter(candidates)), [])
            if len(matches) == 1 and matches[0] != execution_id:
                item["parent_execution_id"] = matches[0]
    return [CodexAgentThread(**item) for item in data.values()]


class AgentThreadTransformation(CodexRecordTransformation):
    """Build thread identities and verified parent relationships."""

    record_type = CodexAgentThread
    destination = ("agent_threads", {name: name for name in CodexAgentThread.__dataclass_fields__})

    def transform(self, records):
        """Return the threads observed in the supplied snapshot."""
        events, _ = _events(records)
        return _threads(events), []


def _project(directory, repository_url):
    if repository_url:
        key = repository_url.strip().rstrip("/")
        if key.lower().endswith(".git"):
            key = key[:-4]
        return key.casefold(), directory or key
    if directory:
        return ntpath.normcase(ntpath.normpath(directory)), directory
    return None, None


class UsageTransformation(CodexRecordTransformation):
    """Calculate deduplicated response usage and conservative legacy deltas."""

    record_type = CodexUsage
    destination = ("usage_records", {name: name for name in CodexUsage.__dataclass_fields__})

    def transform(self, records):
        """Return attributable usage and diagnostics from one raw snapshot."""
        events, diagnostics = _events(records)
        contexts = {}
        turn_contexts = {}
        event_context = {}
        for event in events:
            if not event.thread_id:
                continue
            key = (event.session_id, event.thread_id)
            context = contexts.setdefault(key, {"model": None, "directory": None, "repository_url": None})
            if event.model:
                context["model"] = event.model
            if event.project_path:
                context["directory"] = event.project_path
            if event.repository_url:
                context["repository_url"] = event.repository_url
            if event.turn_id and event.event_type == "turn_context":
                turn_contexts[(key, event.turn_id)] = context.copy()
            event_context[event.record_id] = turn_contexts.get((key, event.turn_id), context).copy()

        response_groups = {}
        partial_owners = set()
        sessions_by_thread = {}
        for event in events:
            if event.thread_id:
                sessions_by_thread.setdefault(event.thread_id, set()).add(event.session_id)
        for event in events:
            usage = (event.token_counters or {}).get("usage")
            if not isinstance(usage, dict):
                continue
            if not event.thread_id or not event.response_id:
                execution_id = _execution_id(event.session_id, event.thread_id) if event.thread_id else None
                if execution_id:
                    partial_owners.add(execution_id)
                diagnostics.append({"source_record_id": event.record_id, "execution_id": execution_id,
                                    "observed_at": _utc(event.timestamp), "message": "Response usage has no verified thread or response ID."})
                continue
            if len(sessions_by_thread[event.thread_id]) != 1:
                diagnostics.append({"source_record_id": event.record_id, "execution_id": None,
                                    "observed_at": _utc(event.timestamp), "message": "Thread has conflicting session identities; usage withheld."})
                continue
            key = (event.thread_id, event.response_id)
            response_groups.setdefault(key, []).append(event)

        rows = []
        for (thread, response), observations in response_groups.items():
            session = observations[0].session_id
            signatures = {json.dumps(item.token_counters["usage"], sort_keys=True) for item in observations}
            execution_id = _execution_id(session, thread)
            if len(signatures) != 1:
                partial_owners.add(execution_id)
                diagnostics.append({"source_record_id": observations[0].record_id, "execution_id": execution_id,
                                    "observed_at": _utc(observations[0].timestamp), "message": "Conflicting response usage observations; usage withheld."})
                continue
            event = observations[0]
            values, complete = calculate_response_usage(event.token_counters["usage"])
            observation_contexts = [event_context.get(item.record_id, {}) for item in observations]
            models = {item.get("model") for item in observation_contexts}
            directories = {item.get("directory") for item in observation_contexts}
            timestamps = {_utc(item.timestamp) for item in observations}
            if len(models) > 1 or len(directories) > 1 or len(timestamps) > 1 or None in timestamps:
                complete = False
                diagnostics.append({"source_record_id": event.record_id, "execution_id": execution_id,
                                    "observed_at": None, "message": "Response attribution or timestamp is incomplete or conflicting."})
            if not complete:
                diagnostics.append({"source_record_id": event.record_id, "execution_id": execution_id,
                                    "observed_at": _utc(event.timestamp), "message": "Response counters are invalid or incomplete."})
            context = observation_contexts[0].copy()
            if len(models) > 1:
                context["model"] = None
            if len(directories) > 1:
                context["directory"] = None
                context["repository_url"] = None
            project_key, project_label = _project(context.get("directory"), context.get("repository_url"))
            rows.append(CodexUsage(hashlib.sha256(json.dumps([thread, response]).encode()).hexdigest(),
                                   event.record_id, execution_id, next(iter(timestamps)) if len(timestamps) == 1 else None, None,
                                   context.get("directory"), project_key, project_label, context.get("model"),
                                   **values, coverage="complete" if complete else "partial", counter_provenance="response"))

        record_logs = {record.record_id: record.log_identity for record in records}
        owner_logs = {}
        response_times = {}
        for event in events:
            if event.thread_id:
                owner = (event.session_id, event.thread_id)
                owner_logs.setdefault(owner, set()).add(record_logs[event.record_id])
                if isinstance((event.token_counters or {}).get("usage"), dict):
                    timestamp = _utc(event.timestamp)
                    response_times.setdefault(owner, []).append(
                        datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else None
                    )
        legacy_events = []
        originals = {}
        response_started = set()
        for event in events:
            if not event.thread_id:
                if event.token_counters:
                    diagnostics.append({"source_record_id": event.record_id, "execution_id": None,
                                        "observed_at": _utc(event.timestamp), "message": "Token owner is unknown; usage withheld."})
                continue
            if len(sessions_by_thread[event.thread_id]) != 1:
                if event.token_counters and not isinstance(event.token_counters.get("usage"), dict):
                    diagnostics.append({"source_record_id": event.record_id, "execution_id": None,
                                        "observed_at": _utc(event.timestamp), "message": "Thread has conflicting session identities; legacy usage withheld."})
                continue
            owner = (event.session_id, event.thread_id)
            if len(owner_logs[owner]) > 1:
                if event.token_counters and not isinstance(event.token_counters.get("usage"), dict):
                    execution_id = _execution_id(*owner)
                    partial_owners.add(execution_id)
                    diagnostics.append({"source_record_id": event.record_id, "execution_id": execution_id,
                                        "observed_at": _utc(event.timestamp), "message": "Legacy counters span multiple source logs; overlap is unknown."})
                continue
            if isinstance((event.token_counters or {}).get("usage"), dict):
                response_started.add(owner)
            if owner in response_started:
                continue
            if event.token_counters and owner in response_times:
                timestamp = _utc(event.timestamp)
                observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else None
                times = response_times[owner]
                if observed is None or any(value is None or observed >= value for value in times):
                    execution_id = _execution_id(*owner)
                    partial_owners.add(execution_id)
                    diagnostics.append({"source_record_id": event.record_id, "execution_id": execution_id,
                                        "observed_at": timestamp, "message": "Legacy and response scopes cannot be ordered reliably."})
                    continue
            execution_id = _execution_id(event.session_id, event.thread_id)
            context = event_context.get(event.record_id, {})
            legacy_events.append(replace(event, reference=event.record_id, session_id=execution_id, model=context.get("model")))
            originals[event.record_id] = event
        accounting = calculate_increments(legacy_events)
        for message in accounting.diagnostics:
            diagnostics.append({"source_record_id": None, "execution_id": None, "observed_at": None, "message": message})
        previous = {}
        for increment in accounting.increments:
            event = originals[increment.reference]
            context = event_context.get(event.record_id, {})
            project_key, project_label = _project(context.get("directory"), context.get("repository_url"))
            values = {name: increment.values.get(name) for name in CodexUsage.__dataclass_fields__
                      if name.endswith("_tokens")}
            rows.append(CodexUsage(event.record_id, event.record_id, increment.session_id, _utc(event.timestamp),
                                   previous.get(increment.session_id), context.get("directory"), project_key,
                                   project_label, increment.model, **values,
                                   coverage="complete" if increment.complete else "partial", counter_provenance="legacy_delta"))
            previous[increment.session_id] = _utc(event.timestamp)
        affected_logs = {record_logs[item["source_record_id"]] for item in diagnostics
                         if item["source_record_id"] in record_logs}
        rows = [replace(row, coverage="partial")
                if row.execution_id in partial_owners or record_logs[row.source_record_id] in affected_logs else row
                for row in rows]
        return rows, diagnostics
