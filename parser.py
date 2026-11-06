"""Read-only discovery and normalization of Codex session JSONL files."""

from collections import Counter
from dataclasses import dataclass, field
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
                diagnostics.append(Diagnostic(str(error.filename or root), None, f"Cannot enumerate directory: {error.strerror}"))

            import os
            for directory, _, files in os.walk(root, onerror=on_error, followlinks=False):
                for name in files:
                    if name.lower().endswith(".jsonl"):
                        path = Path(directory) / name
                        found.setdefault(os.path.normcase(str(path.resolve())), path)
        except OSError as exc:
            diagnostics.append(Diagnostic(str(root), None, f"Cannot enumerate directory: {exc}"))
    return sorted(found.values(), key=lambda path: str(path).casefold())


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _normalize(raw: dict[str, Any], session_id: str, source: Path, line: int, reference: str, metadata: dict[str, str]) -> Event:
    payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
    kind = _string(raw.get("type")) or "unknown"
    subtype = _string(payload.get("type"))
    context = payload if kind in {"session_meta", "turn_context"} else {}
    token_counters = None
    if kind == "token_usage_record":
        token_counters = {key: payload[key] for key in ("usage", "turn_token_usage", "thread_token_usage") if isinstance(payload.get(key), dict)} or None
    elif kind == "event_msg" and subtype == "token_count":
        info = payload.get("info")
        if isinstance(info, dict):
            token_counters = {key: info[key] for key in ("total_token_usage", "last_token_usage") if isinstance(info.get(key), dict)} or None
    evidence = None
    if kind == "event_msg" and subtype in {"collab_agent_spawn", "agent_started", "agent_completed", "skill_invoked"}:
        evidence = {"type": subtype}
        for key in ("agent_id", "parent_agent_id", "thread_id", "receiver_thread_id", "sender_thread_id", "role", "nickname", "skill_name", "started_at", "completed_at", "status"):
            if _string(payload.get(key)):
                evidence[key] = payload[key]
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


def ingest(roots: list[Path]) -> IngestionResult:
    """Read configured sources without modifying them.

    References use session identity, a native event ID when present, and a
    canonical content hash plus its occurrence number within the file. This
    preserves repeated identical events and remains stable on append or move.
    Without session metadata the filename is the fallback session identity.
    """
    result = IngestionResult()
    seen: set[str] = set()
    supported = {"session_meta", "turn_context", "event_msg", "response_item", "token_usage_record"}
    for path in discover_files(roots, result.diagnostics):
        try:
            with path.open("rb") as file:
                lines = file.readlines()
        except OSError as exc:
            result.diagnostics.append(Diagnostic(str(path), None, f"Cannot read source: {exc}"))
            continue
        if not lines:
            result.diagnostics.append(Diagnostic(str(path), None, "Empty source file."))
            continue
        parsed = []
        session_id = None
        metadata: dict[str, str] = {}
        for number, line in enumerate(lines, 1):
            try:
                raw = json.loads(line.decode("utf-8-sig"))
                if not isinstance(raw, dict):
                    raise ValueError("event is not an object")
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                partial = number == len(lines) and not line.endswith((b"\n", b"\r"))
                message = "Incomplete final line" if partial else "Malformed JSON event"
                result.diagnostics.append(Diagnostic(str(path), number, f"{message}: {exc}"))
                continue
            if not isinstance(raw.get("type"), str) or not raw["type"]:
                result.diagnostics.append(Diagnostic(str(path), number, "Event type must be a non-empty string."))
                continue
            try:
                canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                canonical.encode("utf-8")
            except (UnicodeEncodeError, TypeError, ValueError) as exc:
                result.diagnostics.append(Diagnostic(str(path), number, f"Invalid event encoding or content: {exc}"))
                continue
            parsed.append((number, raw))
            payload = raw.get("payload")
            if raw.get("type") == "session_meta" and isinstance(payload, dict):
                source = payload.get("source")
                subagent = source.get("subagent") if isinstance(source, dict) else None
                spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
                if isinstance(spawn, dict):
                    for key in ("parent_thread_id", "agent_role", "agent_nickname"):
                        value = _string(spawn.get(key))
                        if value:
                            metadata[key] = value
                candidate = _string(payload.get("session_id")) or _string(payload.get("id"))
                if candidate and session_id and candidate != session_id:
                    result.diagnostics.append(Diagnostic(str(path), number, "Conflicting session metadata IDs."))
                elif candidate:
                    session_id = candidate
        if not session_id:
            session_id = f"filename:{path.name}"
            result.diagnostics.append(Diagnostic(str(path), None, "Missing session ID; using filename fallback."))
        occurrences: Counter[str] = Counter()
        for number, raw in parsed:
            canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            occurrences[digest] += 1
            payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
            native_id = _string(raw.get("id")) or _string(payload.get("id")) or ""
            identity = json.dumps([session_id, native_id, digest, occurrences[digest]], ensure_ascii=False)
            reference = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            if reference in seen:
                continue
            seen.add(reference)
            event = _normalize(raw, session_id, path, number, reference, metadata)
            result.events.append(event)
            if raw.get("type") not in supported:
                result.diagnostics.append(Diagnostic(str(path), number, f"Unsupported event type: {event.event_type}."))
    return result



