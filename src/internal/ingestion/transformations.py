"""Transform collected Codex records into attributable threads and usage."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
import ntpath
import re

from internal.analytics.token_accounting import _timestamp, calculate_increments, calculate_response_usage
from internal.ingestion.parser import parse_collected


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


def _valid_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    match = re.fullmatch(r"(\d{4}-\d\d-\d\d[Tt ]\d\d:\d\d:\d\d)(\.\d+)?([Zz]|[+-]\d\d:\d\d)", value)
    if not match:
        return None
    try:
        datetime.fromisoformat(match.group(1) + match.group(3).upper().replace("Z", "+00:00"))
        return value
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
                            "observed_at": _valid_timestamp(event.timestamp) if event else None,
                            "message": f"{item.source}:{item.line or '-'}: {item.message}"})
    return parsed.events, diagnostics


def _threads(events):
    data = {}
    parents = {}
    diagnostics = []
    calls = {}
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
        if event.event_type == "session_meta" and event.parent_agent_id:
            parents.setdefault(item["thread_id"], {}).setdefault(event.parent_agent_id, set()).add(event.record_id)
        evidence = event.evidence or {}
        if evidence.get("type") == "collab_agent_spawn":
            sender, receiver = evidence.get("sender_thread_id"), evidence.get("receiver_thread_id")
            if sender and receiver:
                parents.setdefault(receiver, {}).setdefault(sender, set()).add(event.record_id)
        elif evidence.get("type") == "function_call" and evidence.get("name", "").replace("__", ".").split(".")[-1] == "spawn_agent":
            calls[(item["thread_id"], evidence.get("call_id"))] = event.record_id
        elif evidence.get("type") == "function_call_output":
            call_id = evidence.get("call_id")
            child = (evidence.get("output") or {}).get("agent_id")
            call_record = calls.get((item["thread_id"], call_id))
            if call_record and isinstance(child, str) and child:
                parents.setdefault(child, {}).setdefault(item["thread_id"], set()).update((call_record, event.record_id))
    by_thread = {}
    for item in data.values():
        by_thread.setdefault(item["thread_id"], []).append(item["execution_id"])
    for child, candidates in parents.items():
        child_matches = by_thread.get(child, [])
        references = sorted({reference for refs in candidates.values() for reference in refs if reference})
        message = None
        if len(child_matches) != 1:
            message = f"Unresolved child thread {child}."
        elif len(candidates) != 1:
            message = f"Conflicting parent claims for {child}: {', '.join(sorted(candidates))}."
        else:
            parent = next(iter(candidates))
            parent_matches = by_thread.get(parent, [])
            if parent == child:
                message = f"Self-referential parent link for {child}."
            elif len(parent_matches) != 1:
                message = f"Unresolved parent {parent} for thread {child}."
            else:
                data[child_matches[0]]["parent_execution_id"] = parent_matches[0]
        if message:
            diagnostics.append({"source_record_id": references[0] if references else None,
                                "execution_id": child_matches[0] if len(child_matches) == 1 else None,
                                "observed_at": None, "message": f"{message} Evidence: {', '.join(references)}"})
    visited = set()
    for start in data:
        path = []
        positions = {}
        node = start
        while node is not None and node not in visited and node not in positions:
            positions[node] = len(path)
            path.append(node)
            node = data[node]["parent_execution_id"]
        if node in positions:
            for member in path[positions[node]:]:
                child = data[member]["thread_id"]
                parent_id = data[member]["parent_execution_id"]
                parent = data[parent_id]["thread_id"]
                refs = sorted(parents.get(child, {}).get(parent, set()))
                diagnostics.append({"source_record_id": refs[0] if refs else None, "execution_id": member,
                                    "observed_at": None,
                                    "message": f"Cyclic parent link {child} -> {parent} withheld. Evidence: {', '.join(refs)}"})
                data[member]["parent_execution_id"] = None
        visited.update(path)
    return [CodexAgentThread(**item) for item in data.values()], diagnostics


class AgentThreadTransformation(CodexRecordTransformation):
    """Build thread identities and verified parent relationships."""

    record_type = CodexAgentThread
    destination = ("agent_threads", {name: name for name in CodexAgentThread.__dataclass_fields__})

    def transform(self, records):
        """Return the threads observed in the supplied snapshot."""
        events, _ = _events(records)
        return _threads(events)


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
        repositories = {}
        turn_contexts = {}
        event_context = {}
        for event in events:
            if not event.thread_id:
                continue
            key = (event.session_id, event.thread_id)
            context = contexts.setdefault(key, {"model": None, "directory": None, "repository_url": None})
            if event.event_type == "session_meta":
                if event.model:
                    context["model"] = event.model
                if event.project_path:
                    context["directory"] = event.project_path
            if event.project_path and event.repository_url:
                directory_key = ntpath.normcase(ntpath.normpath(event.project_path))
                repositories.setdefault((key, directory_key), set()).add(event.repository_url)
        for event in events:
            if not event.thread_id or event.event_type != "turn_context" or not event.turn_id:
                continue
            key = (event.session_id, event.thread_id)
            context = contexts[key].copy()
            context["model"] = event.model or context["model"]
            context["directory"] = event.project_path or context["directory"]
            turn_key = (key, event.turn_id)
            if turn_key in turn_contexts:
                previous = turn_contexts[turn_key]
                for field in ("model", "directory"):
                    if previous[field] != context[field]:
                        context[field] = None
                        diagnostics.append({"source_record_id": event.record_id,
                                            "execution_id": _execution_id(*key), "observed_at": _valid_timestamp(event.timestamp),
                                            "message": f"Conflicting {field} for turn {event.turn_id}."})
            turn_contexts[turn_key] = context
        for event in events:
            if not event.thread_id:
                continue
            key = (event.session_id, event.thread_id)
            context = turn_contexts.get((key, event.turn_id), contexts[key]).copy()
            directory = context["directory"]
            if directory:
                directory_key = ntpath.normcase(ntpath.normpath(directory))
                candidates = repositories.get((key, directory_key), set())
                if len(candidates) == 1:
                    context["repository_url"] = next(iter(candidates))
                elif len(candidates) > 1:
                    diagnostics.append({"source_record_id": event.record_id, "execution_id": _execution_id(*key),
                                        "observed_at": _valid_timestamp(event.timestamp), "message": "Conflicting repository identities for working directory."})
                    context["project_conflict"] = True
            event_context[event.record_id] = context

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
                                    "observed_at": _valid_timestamp(event.timestamp), "message": "Response usage has no verified thread or response ID."})
                continue
            if len(sessions_by_thread[event.thread_id]) != 1:
                diagnostics.append({"source_record_id": event.record_id, "execution_id": None,
                                    "observed_at": _valid_timestamp(event.timestamp), "message": "Thread has conflicting session identities; usage withheld."})
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
                                    "observed_at": _valid_timestamp(observations[0].timestamp), "message": "Conflicting response usage observations; usage withheld."})
                continue
            event = observations[0]
            values, counters_complete = calculate_response_usage(event.token_counters["usage"])
            complete = counters_complete
            observation_contexts = [event_context.get(item.record_id, {}) for item in observations]
            models = {item.get("model") for item in observation_contexts}
            directories = {item.get("directory") for item in observation_contexts}
            timestamps = {_timestamp(_valid_timestamp(item.timestamp)) for item in observations}
            if len(models) > 1 or len(directories) > 1 or len(timestamps) > 1 or None in timestamps:
                complete = False
                diagnostics.append({"source_record_id": event.record_id, "execution_id": execution_id,
                                    "observed_at": None, "message": "Response attribution or timestamp is incomplete or conflicting."})
            if not counters_complete:
                diagnostics.append({"source_record_id": event.record_id, "execution_id": execution_id,
                                    "observed_at": _valid_timestamp(event.timestamp), "message": "Response counters are invalid or incomplete."})
            context = observation_contexts[0].copy()
            if len(models) > 1:
                context["model"] = None
            if len(directories) > 1:
                context["directory"] = None
                context["repository_url"] = None
            project_key, project_label = (None, None) if context.get("project_conflict") else _project(
                context.get("directory"), context.get("repository_url")
            )
            rows.append(CodexUsage(hashlib.sha256(json.dumps([thread, response]).encode()).hexdigest(),
                                   event.record_id, execution_id, _valid_timestamp(event.timestamp) if len(timestamps) == 1 else None, None,
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
                    timestamp = _valid_timestamp(event.timestamp)
                    response_times.setdefault(owner, []).append(
                        _timestamp(timestamp)
                    )
        legacy_events = []
        originals = {}
        response_started = set()
        for event in events:
            if not event.thread_id:
                if event.token_counters:
                    diagnostics.append({"source_record_id": event.record_id, "execution_id": None,
                                        "observed_at": _valid_timestamp(event.timestamp), "message": "Token owner is unknown; usage withheld."})
                continue
            if len(sessions_by_thread[event.thread_id]) != 1:
                if event.token_counters and not isinstance(event.token_counters.get("usage"), dict):
                    diagnostics.append({"source_record_id": event.record_id, "execution_id": None,
                                        "observed_at": _valid_timestamp(event.timestamp), "message": "Thread has conflicting session identities; legacy usage withheld."})
                continue
            owner = (event.session_id, event.thread_id)
            if len(owner_logs[owner]) > 1:
                if event.token_counters and not isinstance(event.token_counters.get("usage"), dict):
                    execution_id = _execution_id(*owner)
                    partial_owners.add(execution_id)
                    diagnostics.append({"source_record_id": event.record_id, "execution_id": execution_id,
                                        "observed_at": _valid_timestamp(event.timestamp), "message": "Legacy counters span multiple source logs; overlap is unknown."})
                continue
            if isinstance((event.token_counters or {}).get("usage"), dict):
                response_started.add(owner)
            if owner in response_started:
                continue
            if event.token_counters and owner in response_times:
                timestamp = _valid_timestamp(event.timestamp)
                observed = _timestamp(timestamp)
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
            project_key, project_label = (None, None) if context.get("project_conflict") else _project(
                context.get("directory"), context.get("repository_url")
            )
            values = {name: increment.values.get(name) for name in CodexUsage.__dataclass_fields__
                      if name.endswith("_tokens")}
            rows.append(CodexUsage(event.record_id, event.record_id, increment.session_id, _valid_timestamp(event.timestamp),
                                   previous.get(increment.session_id), context.get("directory"), project_key,
                                   project_label, increment.model, **values,
                                   coverage="complete" if increment.complete else "partial", counter_provenance="legacy_delta"))
            previous[increment.session_id] = _valid_timestamp(event.timestamp)
        affected_logs = {record_logs[item["source_record_id"]] for item in diagnostics
                         if item["source_record_id"] in record_logs}
        rows = [replace(row, coverage="partial")
                if row.execution_id in partial_owners or record_logs[row.source_record_id] in affected_logs else row
                for row in rows]
        return rows, diagnostics
