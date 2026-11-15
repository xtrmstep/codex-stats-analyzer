"""Validate response usage and parse recorded timestamps."""

from datetime import datetime
from decimal import Decimal
import re
from typing import Any


FIELDS = ("total_tokens", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "cache_write_input_tokens")


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


