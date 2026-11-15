"""Read-only discovery and normalization of Codex session JSONL files."""

from collections import Counter
from dataclasses import dataclass, field, replace
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Diagnostic:
    """A source location and a description of data that could not be processed."""

    source: str
    line: int | None
    message: str
    fatal: bool = False


@dataclass(frozen=True)
class Event:
    """An observed event with stable identity and source provenance."""

    reference: str
    session_id: str
    source: str
    line: int
    event_type: str
    timestamp: str | None = None
    project_path: str | None = None
    model: str | None = None
    reasoning_effort: str | None = None
    agent_id: str | None = None
    parent_agent_id: str | None = None
    agent_role: str | None = None
    agent_nickname: str | None = None
    token_counters: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    thread_id: str | None = None
    turn_id: str | None = None
    response_id: str | None = None
    record_id: str | None = None
    repository_url: str | None = None


@dataclass
class IngestionResult:
    """Normalized events and diagnostics for a discovery pass."""

    events: list[Event] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)


def discover_files(roots: list[Path], diagnostics: list[Diagnostic]) -> list[Path]:
    """Find JSONL files recursively, avoiding repeated paths from overlapping roots."""
    found: dict[str, Path] = {}
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            diagnostics.append(Diagnostic(str(root), None, "Source directory is missing or inaccessible."))
            continue
        try:
            def on_error(error: OSError) -> None:
                diagnostics.append(Diagnostic(str(error.filename or root), None, f"Cannot enumerate directory: {error.strerror}", fatal=True))

            import os
            for directory, _, files in os.walk(root, onerror=on_error, followlinks=False):
                for name in files:
                    if name.lower().endswith(".jsonl"):
                        path = Path(directory) / name
                        found.setdefault(os.path.normcase(str(path.resolve())), path)
        except OSError as exc:
            diagnostics.append(Diagnostic(str(root), None, f"Cannot enumerate directory: {exc}", fatal=True))
    return sorted(found.values(), key=lambda path: str(path).casefold())


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def read_source_lines(path: Path) -> list[bytes]:
    """Read original lines without decoding or changing their terminators."""
    with path.open("rb") as source:
        return source.readlines()


def _normalize(raw: dict[str, Any], session_id: str, source: Path, line: int, reference: str, metadata: dict[str, str]) -> Event:
    payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
    kind = _string(raw.get("type")) or "unknown"
    subtype = _string(payload.get("type"))
    context = payload if kind in {"session_meta", "turn_context"} else {}
    token_counters = None
    if kind == "token_usage_record":
        token_counters = {"usage": payload["usage"]} if isinstance(payload.get("usage"), dict) else None
    evidence = None
    if kind == "event_msg" and subtype in {"collab_agent_spawn", "agent_started", "agent_completed", "skill_invoked"}:
        evidence = {"type": subtype}
        for key in ("agent_id", "parent_agent_id", "thread_id", "receiver_thread_id", "sender_thread_id", "role", "nickname", "skill_name", "started_at", "completed_at", "status"):
            if _string(payload.get(key)):
                evidence[key] = payload[key]
    if kind == "response_item" and subtype in {"function_call", "function_call_output"}:
        call_id = _string(payload.get("call_id"))
        if call_id:
            evidence = {"type": subtype, "call_id": call_id}
            if subtype == "function_call":
                name = _string(payload.get("name"))
                if name:
                    evidence["name"] = name
                raw_arguments = payload.get("arguments")
                try:
                    arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
                except (ValueError, TypeError):
                    arguments = None
                evidence["arguments_valid"] = isinstance(arguments, dict)
                if isinstance(arguments, dict):
                    evidence["arguments"] = {key: arguments[key] for key in ("task_name", "agent_id") if isinstance(arguments.get(key), str)}
            else:
                raw_output = payload.get("output")
                try:
                    output = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
                except (ValueError, TypeError):
                    output = None
                if isinstance(output, dict):
                    evidence["output"] = {key: output[key] for key in ("task_name", "agent_id", "status", "timed_out") if isinstance(output.get(key), (str, bool))}
    return Event(
        reference=reference, session_id=session_id, source=str(source), line=line,
        event_type=f"{kind}.{subtype}" if subtype else kind,
        timestamp=_string(raw.get("timestamp")) or (_string(payload.get("timestamp")) if kind == "session_meta" else None),
        project_path=_string(context.get("cwd")), model=_string(context.get("model")),
        reasoning_effort=_string(context.get("effort")),
        agent_id=_string(payload.get("agent_id")) or _string(payload.get("thread_id")),
        parent_agent_id=_string(payload.get("parent_agent_id")) or (_string(payload.get("parent_thread_id")) if kind == "session_meta" else None) or metadata.get("parent_thread_id"),
        agent_role=_string(payload.get("agent_role")) or metadata.get("agent_role"), agent_nickname=_string(payload.get("agent_nickname")) or metadata.get("agent_nickname"),
        token_counters=token_counters, evidence=evidence,
    )


def parse_collected(records) -> IngestionResult:
    """Normalize an ordered snapshot of collected lines without source files.

    Args:
        records: Collected records ordered by log identity and line number.

    Returns:
        Events retaining their source record and legacy reference, with diagnostics.
    """
    result = IngestionResult()
    logs: dict[str, list] = {}
    for record in records:
        logs.setdefault(record.log_identity, []).append(record)
    supported = {"session_meta", "turn_context", "event_msg", "response_item", "token_usage_record"}
    for entries in logs.values():
        parsed = []
        sessions, threads = set(), set()
        metadata: dict[str, str] = {}
        for record in entries:
            try:
                raw = json.loads(record.original_line_bytes.decode("utf-8-sig"))
                if not isinstance(raw, dict) or not _string(raw.get("type")):
                    raise ValueError("event is not an object with a type")
                canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                canonical.encode("utf-8")
            except (UnicodeError, ValueError, TypeError) as exc:
                result.diagnostics.append(Diagnostic(record.source_path, record.line_number, f"Invalid or incomplete event: {exc}"))
                continue
            parsed.append((record, raw, canonical))
            payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
            if raw["type"] == "session_meta":
                session = _string(payload.get("session_id")) or _string(payload.get("id"))
                thread = _string(payload.get("id"))
                if session:
                    sessions.add(session)
                if thread:
                    threads.add(thread)
                source = payload.get("source")
                subagent = source.get("subagent") if isinstance(source, dict) else None
                spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
                if isinstance(spawn, dict):
                    for key in ("parent_thread_id", "agent_role", "agent_nickname"):
                        if _string(spawn.get(key)):
                            metadata[key] = spawn[key]
                if _string(payload.get("parent_thread_id")):
                    metadata["parent_thread_id"] = payload["parent_thread_id"]
        source = entries[0].source_path
        session = next(iter(sessions)) if len(sessions) == 1 else f"filename:{Path(source).name}"
        owner = next(iter(threads)) if len(threads) == 1 else None
        if len(sessions) != 1 or len(threads) != 1:
            result.diagnostics.append(Diagnostic(source, None, "Missing or conflicting source identity; ownership may be unknown."))
        occurrences: Counter[str] = Counter()
        for record, raw, canonical in parsed:
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            occurrences[digest] += 1
            payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
            native_id = _string(raw.get("id")) or _string(payload.get("id")) or ""
            identity = json.dumps([session, native_id, digest, occurrences[digest]], ensure_ascii=False)
            reference = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            event = _normalize(raw, session, Path(record.source_path), record.line_number, reference, metadata)
            explicit_thread = _string(payload.get("thread_id")) if raw["type"] == "token_usage_record" else None
            explicit_agent = _string(payload.get("agent_id")) if raw["type"] == "token_usage_record" else None
            if explicit_thread and explicit_agent and explicit_thread != explicit_agent:
                thread = None
                result.diagnostics.append(Diagnostic(record.source_path, record.line_number, "Conflicting token owner IDs."))
            else:
                thread = explicit_thread or explicit_agent or owner
            token_session = _string(payload.get("session_id")) if raw["type"] == "token_usage_record" else None
            if token_session and len(sessions) == 1 and token_session != session and thread == owner:
                thread = None
                result.diagnostics.append(Diagnostic(record.source_path, record.line_number, "Token session conflicts with source metadata; ownership withheld."))
            event_session = token_session or session
            event = replace(event, session_id=event_session, agent_id=thread, thread_id=thread,
                            turn_id=_string(payload.get("turn_id")),
                            response_id=_string(payload.get("response_id")), record_id=record.record_id,
                            repository_url=_string(payload.get("git", {}).get("repository_url"))
                            if isinstance(payload.get("git"), dict) else None)
            if raw["type"] == "session_meta":
                source_meta = payload.get("source")
                subagent = source_meta.get("subagent") if isinstance(source_meta, dict) else None
                spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
                parent = (_string(payload.get("parent_agent_id")) or _string(payload.get("parent_thread_id"))
                          or (_string(spawn.get("parent_thread_id")) if isinstance(spawn, dict) else None))
                event = replace(event, parent_agent_id=parent)
            if thread is None or thread != owner:
                event = replace(event, parent_agent_id=None, agent_role=None, agent_nickname=None)
            result.events.append(event)
            if raw["type"] not in supported:
                result.diagnostics.append(Diagnostic(record.source_path, record.line_number, f"Unsupported event type: {event.event_type}."))
    return result





