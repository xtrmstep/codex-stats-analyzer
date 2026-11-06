"""Explicit agent relationships, observed activity and skill evidence."""

from dataclasses import dataclass, field
from datetime import datetime

from analytics import Increment, Total, aggregate
from parser import Event


@dataclass(frozen=True)
class Activity:
    """Timestamped evidence, distinct from a verified execution interval."""

    first: str | None
    last: str | None
    first_reference: str | None
    last_reference: str | None
    verified_start: str | None = None
    verified_end: str | None = None
    verified_reference: str | None = None


@dataclass
class Agent:
    """One observed thread and its supported properties."""

    id: str
    parent_id: str | None = None
    model: str | None = None
    role: str | None = None
    nickname: str | None = None
    status: str | None = None
    activity: Activity | None = None
    tokens: Total = field(default_factory=lambda: Total(None, False))
    cache_percentage: Total = field(default_factory=lambda: Total(None, False))


@dataclass
class AgentAnalysis:
    """Evidence-backed hierarchy and metrics for a selected root thread."""

    agents: dict[str, Agent]
    children: dict[str, list[str]]
    unlinked: list[str]
    participating_count: int
    max_depth: int | None
    main_tokens: Total
    subagent_tokens: Total
    subagent_share: Total
    skills: list[dict[str, str]]
    diagnostics: list[str]


def _time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.utcoffset() is not None else None
    except ValueError:
        return None


def analyze_agents(root_id: str, events: list[Event], increments: list[Increment]) -> AgentAnalysis:
    """Build a tree from explicit parent metadata and coordination evidence.

    Args:
        root_id: Session/thread ID selected as the root.
        events: Normalized source events, including other observed threads.
        increments: Accounting increments from the same source events.

    Returns:
        Hierarchy, unlinked threads, evidence and coverage-aware metrics.
    """
    agents: dict[str, Agent] = {}
    parents: dict[str, set[str]] = {}
    activity: dict[str, list[tuple[datetime, str, str]]] = {}
    verified: dict[str, tuple[str, str, str]] = {}
    skills: list[dict[str, str]] = []
    diagnostics: list[str] = []
    pending_status: list[tuple[str, str, dict, str]] = []
    calls: dict[tuple[str, str], tuple[str, dict]] = {}
    outputs: list[tuple[str, str, dict, str]] = []
    for event in events:
        agent = agents.setdefault(event.session_id, Agent(event.session_id))
        for attr, value in (("model", event.model), ("role", event.agent_role), ("nickname", event.agent_nickname)):
            if value:
                setattr(agent, attr, value)
        if event.parent_agent_id:
            parents.setdefault(agent.id, set()).add(event.parent_agent_id)
        timestamp = _time(event.timestamp)
        if timestamp:
            activity.setdefault(agent.id, []).append((timestamp, event.timestamp, event.reference))
        evidence = event.evidence or {}
        kind = evidence.get("type")
        if kind == "function_call":
            call_id, name = evidence.get("call_id"), evidence.get("name")
            if isinstance(call_id, str) and isinstance(name, str):
                short_name = name.replace("__", ".").split(".")[-1]
                if short_name in {"spawn_agent", "wait_agent"}:
                    calls[(agent.id, call_id)] = (short_name, evidence.get("arguments", {}))
                    if not evidence.get("arguments_valid", False):
                        diagnostics.append(f"{event.reference}: {short_name} arguments are malformed or unavailable.")
        elif kind == "function_call_output":
            call_id = evidence.get("call_id")
            if isinstance(call_id, str):
                outputs.append((agent.id, call_id, evidence.get("output", {}), event.reference))
        elif kind == "collab_agent_spawn":
            sender = evidence.get("sender_thread_id")
            receiver = evidence.get("receiver_thread_id")
            if isinstance(sender, str) and isinstance(receiver, str) and sender and receiver:
                parents.setdefault(receiver, set()).add(sender)
        elif kind == "skill_invoked":
            name = evidence.get("skill_name")
            if isinstance(name, str) and name:
                skills.append({"agent_id": agent.id, "name": name, "reference": event.reference})
        elif kind in {"agent_started", "agent_completed"}:
            target = evidence.get("agent_id") or evidence.get("thread_id")
            if not isinstance(target, str) or not target:
                diagnostics.append(f"{event.reference}: agent status has no explicit target; attribution withheld.")
            else:
                # Resolve after all events have established which threads exist.
                pending_status.append((target, kind, evidence, event.reference))
    for source_id, call_id, output, reference in outputs:
        call = calls.get((source_id, call_id))
        if not call:
            continue
        name, arguments = call
        if not isinstance(output, dict) or not output:
            diagnostics.append(f"{reference}: {name} result is missing or unsupported.")
            continue
        if name == "spawn_agent":
            child = output.get("agent_id")
            task = output.get("task_name")
            if isinstance(child, str) and child:
                agents.setdefault(child, Agent(child))
                parents.setdefault(child, set()).add(source_id)
            elif isinstance(task, str) and task:
                child = f"task:{task}"
                agents.setdefault(child, Agent(child, nickname=task))
                parents.setdefault(child, set()).add(source_id)
                diagnostics.append(f"{reference}: spawned task has no thread ID; association with session files is unknown.")
            else:
                diagnostics.append(f"{reference}: spawn result has no explicit agent identifier.")
        elif name == "wait_agent" and output.get("timed_out") is True:
            diagnostics.append(f"{reference}: wait timed out; agent status remains unknown.")
    for target, kind, evidence, reference in pending_status:
        if target not in agents:
            diagnostics.append(f"{reference}: status target {target} is unobserved; attribution withheld.")
            continue
        agent = agents[target]
        if kind == "agent_started":
            agent.status = "running"
        else:
            agent.status = evidence.get("status") if isinstance(evidence.get("status"), str) else "completed"
            start, end = evidence.get("started_at"), evidence.get("completed_at")
            if isinstance(start, str) and isinstance(end, str) and _time(start) and _time(end) and _time(start) <= _time(end):
                verified[target] = (start, end, reference)
    if root_id not in agents:
        diagnostics.append(f"Root {root_id} has no observed events.")
    for child, candidates in parents.items():
        if child not in agents:
            diagnostics.append(f"Parent link references unobserved agent {child}.")
        elif len(candidates) != 1:
            diagnostics.append(f"Agent {child} has conflicting parents; link withheld.")
        else:
            parent = next(iter(candidates))
            if parent not in agents:
                diagnostics.append(f"Agent {child} has missing parent {parent}; link withheld.")
            else:
                agents[child].parent_id = parent
    for agent in agents.values():
        path: set[str] = set()
        cursor = agent.id
        while cursor in agents and agents[cursor].parent_id:
            if cursor in path:
                diagnostics.append(f"Cycle involving {cursor}; links in cycle withheld.")
                cycle_start = cursor
                while True:
                    next_id = agents[cursor].parent_id
                    agents[cursor].parent_id = None
                    cursor = next_id
                    if cursor == cycle_start:
                        break
                break
            path.add(cursor)
            cursor = agents[cursor].parent_id
    children = {agent_id: [] for agent_id in agents}
    for agent in agents.values():
        if agent.parent_id:
            children[agent.parent_id].append(agent.id)
    for child_list in children.values():
        child_list.sort()
    depths: dict[str, int] = {}
    if root_id in agents:
        stack = [(root_id, 0)]
        while stack:
            agent_id, depth = stack.pop()
            depths[agent_id] = depth
            stack.extend((child, depth + 1) for child in children[agent_id])
    unlinked = sorted(set(agents) - set(depths))
    for agent_id, agent in agents.items():
        points = sorted(activity.get(agent_id, []))
        interval = verified.get(agent_id)
        agent.activity = Activity(points[0][1] if points else None, points[-1][1] if points else None,
                                  points[0][2] if points else None, points[-1][2] if points else None,
                                  *(interval or (None, None, None)))
        totals = aggregate([i for i in increments if i.session_id == agent_id])
        agent.tokens = totals["total_tokens"]
        agent.cache_percentage = totals["cache_percentage"]
    main = agents[root_id].tokens if root_id in agents else Total(None, False)
    child_ids = set(depths) - {root_id}
    child_increments = [i for i in increments if i.session_id in child_ids]
    stream_ids = {increment.session_id for increment in child_increments}
    nested_streams = False
    for child in stream_ids:
        ancestor = agents[child].parent_id
        visited = {child}
        while ancestor in child_ids and ancestor not in visited:
            if ancestor in stream_ids:
                nested_streams = True
                break
            visited.add(ancestor)
            ancestor = agents[ancestor].parent_id
        if nested_streams:
            break
    sub = (Total(None, False) if nested_streams else
           aggregate(child_increments)["total_tokens"] if child_ids else Total(None, False))
    if nested_streams:
        diagnostics.append("Nested agent counter scopes may overlap; combined subagent tokens are unknown.")
    if child_ids and (any(not any(i.session_id == child for i in child_increments) for child in child_ids)):
        sub = Total(sub.value, False)
    # Parent counters may already include child counters, so a combined share
    # is not meaningful until their counter scope is established.
    share = Total(None, False)
    return AgentAnalysis(agents, children, unlinked, len(depths), max(depths.values()) if depths else None,
                         main, sub, share, skills, diagnostics)





