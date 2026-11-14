"""Saved experiment definitions and manual history snapshots."""

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from internal.metadata.experiments import Group
from internal.analytics.metrics import Filters

METRICS = ("mean_tokens", "median_tokens", "output_tokens", "cache_percentage", "subagent_share", "elapsed_seconds", "success_rate", "evaluation_score")
FILTER_FIELDS = ("label_ids", "task_types", "execution_modes", "projects", "models", "sessions", "agent_roles")


def validate_experiment(item):
    """Validate a saved definition and optional recorded history."""
    groups = item.get("groups")
    metrics = item.get("metrics")
    if not isinstance(groups, list) or not isinstance(metrics, list):
        raise ValueError("Experiment groups and metrics must be lists.")
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("name"), str) or not group["name"].strip():
            raise ValueError("Each group needs a non-empty name.")
        filters = group.get("filters", {})
        if not isinstance(filters, dict):
            raise ValueError("Group filters must be an object.")
        for field in FILTER_FIELDS:
            value = filters.get(field)
            if value is not None and (not isinstance(value, list) or not all(isinstance(x, str) and x for x in value)):
                raise ValueError(f"Group {field} must be a list of strings or null.")
        if filters.get("label_mode", "all") not in ("all", "any"):
            raise ValueError("Group label mode must be all or any.")
    if not all(isinstance(metric, str) and metric for metric in metrics):
        raise ValueError("Experiment metrics must be non-empty strings.")
    history = item.get("history", [])
    if not isinstance(history, list):
        raise ValueError("Experiment history must be a list.")
    for snapshot in history:
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("recorded_at"), str) or not isinstance(snapshot.get("groups"), list) or not isinstance(snapshot.get("global_filters"), dict):
            raise ValueError("History snapshots require recorded_at, groups and global_filters.")
        try:
            parsed = datetime.fromisoformat(snapshot["recorded_at"].replace("Z", "+00:00"))
            if parsed.utcoffset() is None:
                raise ValueError
        except ValueError as exc:
            raise ValueError("History timestamps must include a timezone.") from exc
        for group in snapshot["groups"]:
            if not isinstance(group, dict) or not isinstance(group.get("name"), str) or not isinstance(group.get("run_count"), int) or isinstance(group.get("run_count"), bool) or group["run_count"] < 0 or not isinstance(group.get("measures"), dict):
                raise ValueError("History group data is invalid.")
            for key, measure in group["measures"].items():
                if key not in METRICS or not isinstance(measure, dict) or "value" not in measure or not isinstance(measure.get("eligible"), int) or isinstance(measure.get("eligible"), bool) or not 0 <= measure["eligible"] <= group["run_count"] or (measure.get("value") is not None and (isinstance(measure["value"], bool) or not isinstance(measure["value"], (int, float)))):
                    raise ValueError("History measure data is invalid.")


def groups_from_definition(item):
    """Convert persisted definitions into comparison-engine filters."""
    output = []
    for group in item["groups"]:
        config = group.get("filters", {})
        values = {field: frozenset(config[field]) if config.get(field) is not None else None for field in FILTER_FIELDS}
        values["label_mode"] = config.get("label_mode", "all")
        output.append(Group(group["name"], Filters(**values)))
    return output


def upsert_experiment(data, item):
    """Save a definition, clearing history when group or metric definitions change."""
    item = deepcopy(item)
    item.setdefault("id", str(uuid4()))
    if not isinstance(item.get("name"), str) or not item["name"].strip():
        raise ValueError("Experiment needs a name.")
    validate_experiment(item)
    groups_from_definition(item)
    names = [group["name"].casefold() for group in item["groups"]]
    if len(names) < 2 or len(set(names)) != len(names) or not item["metrics"]:
        raise ValueError("Choose at least two uniquely named groups and one metric.")
    for index, old in enumerate(data["experiments"]):
        if old["id"] == item["id"]:
            if old["groups"] != item["groups"] or old["metrics"] != item["metrics"]:
                item["history"] = []
            data["experiments"][index] = item
            break
    else:
        item.setdefault("history", [])
        data["experiments"].append(item)
    return item["id"]


def record_snapshot(item, comparison, global_filters):
    """Append an explicit timestamped calculation with its global filter context."""
    if any(metric not in METRICS for metric in item["metrics"]):
        raise ValueError("Remove unsupported metrics before recording history.")
    snapshot = {"recorded_at": datetime.now(timezone.utc).isoformat(), "global_filters": global_filters,
                "groups": [{"name": group.name, "run_count": len(group.run_ids),
                            "measures": {key: {"value": group.measures[key].value, "eligible": group.measures[key].eligible}
                                         for key in item["metrics"]}}
                           for group in comparison.groups]}
    item.setdefault("history", []).append(snapshot)
    validate_experiment(item)



