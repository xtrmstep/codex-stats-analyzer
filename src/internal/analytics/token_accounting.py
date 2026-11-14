"""Conservative token counter increments and coverage-aware aggregation."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import re
from typing import Any

from internal.ingestion.parser import Event

FIELDS = ("total_tokens", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "cache_write_input_tokens")


@dataclass(frozen=True)
class Increment:
    """Token changes attributed to an observed counter event."""

    reference: str
    session_id: str
    agent_id: str | None
    parent_agent_id: str | None
    model: str | None
    timestamp: str | None
    values: dict[str, int | None]
    complete: bool
    timing: str = "observed at counter event; usage may precede timestamp"
    thread_id: str | None = None


@dataclass(frozen=True)
class Total:
    """A sum of known values and whether all included increments are covered."""

    value: int | None
    complete: bool


@dataclass
class AccountingResult:
    """Derived increments and explanations of uncertain or invalid data."""

    increments: list[Increment] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


def _timestamp(value: str | None) -> tuple[datetime, Decimal] | None:
    if not value:
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00").replace("z", "+00:00"))
        if result.utcoffset() is None:
            return None
        fraction = re.search(r"[.,](\d+)(?=[Zz]|[+-]\d\d(?::?\d\d)?$)", value)
        precision = Decimal("0." + fraction.group(1)) if fraction else Decimal(result.microsecond) / 1000000
        return result.replace(microsecond=0), precision
    except ValueError:
        return None


def _counter(event: Event, family: str) -> dict[str, Any] | None:
    data = event.token_counters or {}
    value = data.get(family)
    return value if isinstance(value, dict) else None


def calculate_response_usage(counters: dict[str, Any]) -> tuple[dict[str, int | None], bool]:
    """Validate one per-response usage record without combining counter streams."""
    names = FIELDS
    values = {}
    valid = True
    for name in names:
        value = counters.get(name)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            value, valid = None, False
        values[name] = value
    for child, parent in (("cached_input_tokens", "input_tokens"), ("reasoning_output_tokens", "output_tokens")):
        if values[child] is not None and values[parent] is not None and values[child] > values[parent]:
            values[child], valid = None, False
    if all(values[name] is not None for name in ("input_tokens", "output_tokens", "total_tokens")):
        if values["input_tokens"] + values["output_tokens"] != values["total_tokens"]:
            values["total_tokens"], valid = None, False
    values["non_cached_input_tokens"] = (values["input_tokens"] - values["cached_input_tokens"]
                                          if values["input_tokens"] is not None and values["cached_input_tokens"] is not None
                                          else None)
    return values, valid and all(values[name] is not None for name in ("input_tokens", "output_tokens", "total_tokens"))


def calculate_increments(events: list[Event]) -> AccountingResult:
    """Derive changes from one cumulative counter family per session.

    Events must be in source order. A counter decrease starts an uncertain new
    epoch; its current value is counted but coverage is partial. Timestamp
    regressions are excluded without advancing the prior counter.
    """
    result = AccountingResult()
    by_session: dict[tuple[str, str], list[Event]] = {}
    for event in events:
        by_session.setdefault((event.session_id, event.thread_id or event.session_id), []).append(event)
    for (session, thread), session_events in by_session.items():
        families = ("total_token_usage", "thread_token_usage")
        family = next((name for name in families if any(_counter(e, name) is not None for e in session_events)), None)
        if family is None:
            if any(e.token_counters for e in session_events):
                result.diagnostics.append(f"{session}: no supported cumulative counter; usage remains unknown.")
            continue
        if any(_counter(e, name) is not None for e in session_events for name in families if name != family):
            result.diagnostics.append(f"{session}: multiple counter families observed; using {family} only because overlap is unresolved.")
        previous: dict[str, int | None] = {key: None for key in FIELDS}
        previous_time = None
        current_model = None
        previous_model = None
        model_changed = False
        seen: set[str] = set()
        first = True
        for event in session_events:
            if event.model:
                if current_model is not None and event.model != current_model:
                    model_changed = True
                current_model = event.model
            counters = _counter(event, family)
            if counters is None or event.reference in seen:
                continue
            seen.add(event.reference)
            observed_time = _timestamp(event.timestamp)
            if previous_time and observed_time and observed_time < previous_time:
                result.diagnostics.append(f"{event.reference}: out-of-order counter excluded.")
                continue
            values: dict[str, int | None] = {}
            raw: dict[str, int | None] = {}
            valid = True
            for key in FIELDS:
                value = counters.get(key)
                if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                    result.diagnostics.append(f"{event.reference}: invalid {key} counter.")
                    value = None
                    valid = False
                raw[key] = value
            for child, parent in (("cached_input_tokens", "input_tokens"), ("reasoning_output_tokens", "output_tokens")):
                if raw[child] is not None and raw[parent] is not None and raw[child] > raw[parent]:
                    result.diagnostics.append(f"{event.reference}: {child} exceeds {parent}.")
                    raw[child] = None
                    valid = False
            if all(raw[key] is not None for key in ("total_tokens", "input_tokens", "output_tokens")) and raw["total_tokens"] != raw["input_tokens"] + raw["output_tokens"]:
                result.diagnostics.append(f"{event.reference}: total differs from input plus output.")
                valid = False
            reset = any(raw[key] is not None and previous[key] is not None and raw[key] < previous[key] for key in FIELDS)
            if reset:
                result.diagnostics.append(f"{event.reference}: counter decreased; reset or reordering is uncertain.")
            for key in FIELDS:
                if raw[key] is None:
                    values[key] = None
                elif first or reset:
                    values[key] = raw[key]
                elif previous[key] is None:
                    values[key] = None
                else:
                    values[key] = raw[key] - previous[key]
            if (values["reasoning_output_tokens"] is not None
                    and values["output_tokens"] is not None
                    and values["reasoning_output_tokens"] > values["output_tokens"]):
                result.diagnostics.append(f"{event.reference}: reasoning output increment exceeds output increment.")
                values["reasoning_output_tokens"] = None
                valid = False
            if (all(values[key] is not None for key in ("total_tokens", "input_tokens", "output_tokens"))
                    and values["total_tokens"] != values["input_tokens"] + values["output_tokens"]):
                result.diagnostics.append(f"{event.reference}: total increment differs from input plus output increments.")
                values["total_tokens"] = None
                valid = False
            if values["input_tokens"] is not None and values["cached_input_tokens"] is not None and values["cached_input_tokens"] <= values["input_tokens"]:
                values["non_cached_input_tokens"] = values["input_tokens"] - values["cached_input_tokens"]
            else:
                values["non_cached_input_tokens"] = None
                if values["input_tokens"] is not None and values["cached_input_tokens"] is not None:
                    result.diagnostics.append(f"{event.reference}: cached input increment exceeds input increment.")
                    values["cached_input_tokens"] = None
                    valid = False
            model = current_model if not first and not model_changed and current_model == previous_model else None
            if not first and (model_changed or current_model != previous_model):
                result.diagnostics.append(f"{event.reference}: model changed between counters; increment model is unknown.")
            complete = valid and not first and not reset and all(
                value is not None for key, value in values.items() if key != "cache_write_input_tokens"
            )
            result.increments.append(Increment(event.reference, session, event.thread_id or event.agent_id or thread, event.parent_agent_id, model, event.timestamp, values, complete, thread_id=event.thread_id))
            previous = raw
            previous_model = current_model
            model_changed = False
            previous_time = observed_time or previous_time
            first = False
    return result


def aggregate(increments: list[Increment]) -> dict[str, Total]:
    """Sum known values, retaining partial coverage and safe cache percentage.

    Multiple related agent streams are not combined because parent rollup
    semantics are unverified; their aggregate values remain unknown.
    """
    fields = (*FIELDS, "non_cached_input_tokens")
    agents = {i.agent_id for i in increments}
    if len(agents) > 1 and any(i.parent_agent_id in agents for i in increments):
        return {key: Total(None, False) for key in (*fields, "cache_percentage")}
    totals = {}
    for key in fields:
        known = [i.values[key] for i in increments if i.values.get(key) is not None]
        totals[key] = Total(sum(known) if known else None, bool(increments) and len(known) == len(increments) and all(i.complete for i in increments))
    eligible = [i for i in increments if i.values.get("input_tokens") is not None and i.values.get("cached_input_tokens") is not None]
    denominator = sum(i.values["input_tokens"] for i in eligible)
    numerator = sum(i.values["cached_input_tokens"] for i in eligible)
    totals["cache_percentage"] = Total(100 * numerator / denominator if denominator else None, bool(denominator) and len(eligible) == len(increments) and all(i.complete for i in increments))
    return totals




