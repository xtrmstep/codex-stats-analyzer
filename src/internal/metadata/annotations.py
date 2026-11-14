"""Versioned, atomic local storage for annotations and comparisons."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from internal.metadata.runs import validate_run
from internal.metadata.experiment_store import validate_experiment

SCHEMA_VERSION = 1


class StorageError(Exception):
    """Metadata could not safely be read or saved."""


class ConflictError(StorageError):
    """Another writer changed the store or holds its lock."""


@dataclass(frozen=True)
class Snapshot:
    """A loaded document and the revision required for its next save."""

    data: dict[str, Any]
    revision: str | None


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate(data: Any, kind: str) -> None:
    if not isinstance(data, dict):
        raise StorageError("Metadata must be a JSON object.")
    if type(data.get("schema_version")) is not int or data["schema_version"] != SCHEMA_VERSION:
        raise StorageError(f"Unsupported metadata schema version {data.get('schema_version')!r}; preserve the file and use a compatible application version.")
    fields = ("labels", "assignments", "runs") if kind == "annotations" else ("experiments",)
    for name in fields:
        if not isinstance(data.get(name), list) or not all(isinstance(row, dict) for row in data[name]):
            raise StorageError(f"{name} must be a list of objects.")
    for name in ("labels", "runs") if kind == "annotations" else ("experiments",):
        ids: set[str] = set()
        for item in data[name]:
            identifier = item.get("id")
            if not _text(identifier) or identifier in ids:
                raise StorageError(f"{name} must have unique non-empty string IDs.")
            ids.add(identifier)
            if not _text(item.get("name")):
                raise StorageError(f"Each {name} entry needs a non-empty name.")
    if kind == "annotations":
        for label in data["labels"]:
            key = label.get("key", "")
            value = label.get("value", "")
            if (not isinstance(key, str) or not isinstance(value, str)
                    or bool(key.strip()) != bool(value.strip())):
                raise StorageError("Label key and value must both be non-empty strings or both omitted/empty.")
        label_ids = {item["id"] for item in data["labels"]}
        for assignment in data["assignments"]:
            labels = assignment.get("label_ids")
            if (assignment.get("target_type") not in ("session", "run")
                    or not _text(assignment.get("target_id"))
                    or not isinstance(labels, list)
                    or not all(_text(label) for label in labels)
                    or len(set(labels)) != len(labels)
                    or not set(labels).issubset(label_ids)):
                raise StorageError("Assignments require a session or run ID and unique existing label IDs.")
        for run in data["runs"]:
            try:
                validate_run(run)
            except ValueError as exc:
                raise StorageError(f"Invalid run: {exc}") from exc
    else:
        for experiment in data["experiments"]:
            try:
                validate_experiment(experiment)
            except ValueError as exc:
                raise StorageError(f"Invalid experiment: {exc}") from exc
    try:
        json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise StorageError(f"Metadata contains invalid JSON values: {exc}") from exc


def _empty(kind: str) -> dict[str, Any]:
    if kind == "annotations":
        return {"schema_version": SCHEMA_VERSION, "labels": [], "assignments": [], "runs": []}
    return {"schema_version": SCHEMA_VERSION, "experiments": []}


class MetadataStore:
    """A single JSON document with optimistic revisions and cooperative locks."""

    def __init__(self, path: Path, kind: str):
        """Configure an annotations or experiments store without touching disk."""
        if kind not in {"annotations", "experiments"}:
            raise ValueError("Store kind must be annotations or experiments.")
        self.path = Path(path)
        self.kind = kind
        self.lock_path = self.path.with_name(self.path.name + ".lock")

    def load(self) -> Snapshot:
        """Read and validate metadata, or return a new in-memory empty store.

        Raises:
            StorageError: If an existing file cannot be decoded or validated.
        """
        try:
            raw = self.path.read_bytes()
        except FileNotFoundError:
            return Snapshot(_empty(self.kind), None)
        except OSError as exc:
            raise StorageError(f"Cannot read {self.path}: {exc}") from exc
        try:
            data = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageError(f"Cannot read metadata in {self.path}: {exc}. Preserve or restore the file before saving.") from exc
        try:
            _validate(data, self.kind)
        except StorageError as exc:
            raise StorageError(f"Invalid metadata in {self.path}: {exc}") from exc
        return Snapshot(data, hashlib.sha256(raw).hexdigest())

    def save(self, data: dict[str, Any], revision: str | None) -> Snapshot:
        """Validate and atomically replace the file if its revision is unchanged.

        A lock serializes cooperating writers. A lock left by an interrupted
        process must be inspected and removed manually before trying again.

        Raises:
            ConflictError: If another writer holds the lock or changed the file.
            StorageError: If validation or saving fails.
        """
        _validate(data, self.kind)
        temporary: str | None = None
        lock_fd: int | None = None
        error: StorageError | None = None
        result: Snapshot | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                lock_fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise ConflictError(f"Metadata is locked: {self.lock_path}. If no writer is active, inspect and remove the stale lock.") from exc
            current = self.load()
            if current.revision != revision:
                raise ConflictError(f"Metadata changed since it was read: {self.path}. Reload before saving.")
            encoded = (json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8")
            with tempfile.NamedTemporaryFile(mode="wb", dir=self.path.parent, prefix=self.path.name + ".", suffix=".tmp", delete=False) as file:
                temporary = file.name
                file.write(encoded)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
            temporary = None
            result = Snapshot(json.loads(encoded), hashlib.sha256(encoded).hexdigest())
        except StorageError as exc:
            error = exc
        except OSError as exc:
            error = StorageError(f"Cannot save {self.path}; previous metadata was preserved: {exc}")
        cleanup_errors = []
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_errors.append(f"temporary file {temporary}: {exc}")
        if lock_fd is not None:
            try:
                os.close(lock_fd)
            except OSError as exc:
                cleanup_errors.append(f"lock handle {self.lock_path}: {exc}")
            try:
                os.unlink(self.lock_path)
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_errors.append(f"lock file {self.lock_path}: {exc}")
        if cleanup_errors:
            message = "; ".join(cleanup_errors)
            if error is not None:
                error.args = (f"{error} Cleanup also failed: {message}",)
            else:
                error = StorageError(f"Metadata was saved, but cleanup failed: {message}")
        if error is not None:
            raise error
        return result

def missing_sessions(snapshot: Snapshot, available_session_ids: set[str]) -> set[str]:
    """Report referenced source sessions absent from the current discovery pass."""
    references = {run["session_id"] for run in snapshot.data.get("runs", [])}
    references.update(item["target_id"] for item in snapshot.data.get("assignments", []) if item["target_type"] == "session")
    return references - available_session_ids





