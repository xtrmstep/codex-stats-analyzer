"""Manual label definitions, assignments and classification rules."""

from uuid import uuid4


def _canonical(name, key, value):
    name = name.strip()
    key = key.strip()
    value = value.strip()
    if not name:
        raise ValueError("Label name is required.")
    if bool(key) != bool(value):
        raise ValueError("Structured labels require both a key and a value.")
    return name, key, value


def upsert_label(data, name, key="", value="", label_id=None):
    """Create or edit a label, retaining its ID and all assignments on edit."""
    name, key, value = _canonical(name, key, value)
    for item in data["labels"]:
        if item["id"] != label_id and (item["name"].casefold() == name.casefold()
            or (key and item.get("key", "").casefold() == key.casefold()
                and item.get("value", "").casefold() == value.casefold())):
            raise ValueError("A label with that name or structured key/value already exists.")
    if label_id is None:
        label_id = str(uuid4())
        data["labels"].append({"id": label_id, "name": name, "key": key, "value": value})
    else:
        target = next((item for item in data["labels"] if item["id"] == label_id), None)
        if target is None:
            raise ValueError("Label no longer exists.")
        target.update(name=name, key=key, value=value)
    return label_id


def delete_label(data, label_id):
    """Delete a label and remove its ID from every assignment."""
    if not any(item["id"] == label_id for item in data["labels"]):
        raise ValueError("Label no longer exists.")
    data["labels"] = [item for item in data["labels"] if item["id"] != label_id]
    for assignment in data["assignments"]:
        assignment["label_ids"] = [value for value in assignment["label_ids"] if value != label_id]
    data["assignments"] = [item for item in data["assignments"] if item["label_ids"]]


def assign_labels(data, target_type, target_ids, label_ids, action="add"):
    """Add or remove label IDs across multiple explicit sessions or runs."""
    if target_type not in ("session", "run") or action not in ("add", "remove"):
        raise ValueError("Invalid assignment type or action.")
    targets = set(target_ids)
    chosen = set(label_ids)
    if not targets or not all(isinstance(item, str) and item.strip() for item in targets):
        raise ValueError("Select at least one target.")
    if not chosen or not chosen <= {item["id"] for item in data["labels"]}:
        raise ValueError("Select at least one existing label.")
    if target_type == "run" and not targets <= {item["id"] for item in data["runs"]}:
        raise ValueError("A selected run no longer exists.")
    for target in targets:
        matching = [a for a in data["assignments"] if a["target_type"] == target_type and a["target_id"] == target]
        existing = set().union(*(set(a["label_ids"]) for a in matching)) if matching else set()
        updated = (existing | chosen) if action == "add" else (existing - chosen)
        data["assignments"] = [a for a in data["assignments"] if a not in matching]
        if updated:
            data["assignments"].append({"target_type": target_type, "target_id": target, "label_ids": sorted(updated)})


def assigned(data, target_type, target_id):
    """Return explicitly assigned IDs, merging any duplicate assignment rows."""
    return {label for item in data["assignments"] if item["target_type"] == target_type
            and item["target_id"] == target_id for label in item["label_ids"]}


def run_labels(data, run):
    """Return run-explicit and inherited session label IDs separately."""
    explicit = assigned(data, "run", run["id"])
    inherited = assigned(data, "session", run["session_id"]) - explicit
    return explicit, inherited


def matches(data, label_ids, required=None, mode="all", task_types=None, execution_modes=None, run=None):
    """Match label choices and manual classification; run metadata takes precedence."""
    if mode not in ("all", "any"):
        raise ValueError("Label match mode must be all or any.")
    if required is not None:
        wanted = set(required)
        if not wanted or (not wanted <= label_ids if mode == "all" else not bool(wanted & label_ids)):
            return False
    definitions = {label["id"]: label for label in data["labels"]}
    for key, selected in (("task_type", task_types), ("execution_mode", execution_modes)):
        if selected is None:
            continue
        direct = run.get(key) if run else None
        values = {direct} if isinstance(direct, str) and direct.strip() else {
            definitions[label].get("value") for label in label_ids if label in definitions
            and definitions[label].get("key", "").casefold() == key}
        if not values.intersection(selected):
            return False
    return True
