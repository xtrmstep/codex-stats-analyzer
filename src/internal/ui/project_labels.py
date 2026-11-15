"""Derive compact, distinct display names for recorded projects."""

from collections import defaultdict
from hashlib import sha256
import ntpath
import re
from typing import NamedTuple
from urllib.parse import urlsplit

from internal.ingestion.transformations import _project


class ProjectLabel(NamedTuple):
    """Display label and full recorded project identifier."""

    label: str
    identifier: str


def _components(identifier, repository):
    """Return the leaf and nearest-first distinguishing context."""
    if repository:
        if "://" in identifier:
            parsed = urlsplit(identifier)
            parts = [part for part in parsed.path.split("/") if part]
            context = [parsed.hostname or parsed.netloc] if parsed.netloc else []
        else:
            host, _, path = identifier.partition(":")
            parts = [part for part in path.replace("\\", "/").split("/") if part]
            context = [host.rsplit("@", 1)[-1]] if host else []
        if parts:
            leaf = re.sub(r"(?i)\.git$", "", parts[-1]) or parts[-1]
            return leaf, list(reversed(parts[:-1])) + context
        return context[0] if context else identifier, []

    drive, path = ntpath.splitdrive(identifier.replace("/", "\\"))
    parts = [part for part in path.split("\\") if part]
    anchor = drive or ("/" if identifier.startswith("/") else "")
    if not parts:
        return anchor or identifier, []
    return parts[-1], list(reversed(parts[:-1])) + ([anchor] if anchor else [])


def project_labels(rows):
    """Return stable labels and full identifiers keyed by project identity.

    Args:
        rows: Snapshot rows containing project keys and source directories.

    Returns:
        A mapping from each known project key to its display information.
    """
    directories = defaultdict(set)
    for row in rows:
        key = row["project_key"]
        if key is None:
            continue
        directory = row["source_working_directory"]
        if directory and _project(directory, None)[0] == key:
            directories[key].add(directory)
        else:
            directories[key]  # Keep keys without a matching folder.

    items = {}
    for key, paths in directories.items():
        identifier = min(paths, key=lambda value: (value.casefold(), value)) if paths else key
        repository = not paths and ("://" in key or
                                    bool(re.match(r"^(?![a-zA-Z]:[\\/])[^/\\:]+:.+", key)))
        leaf, context = _components(identifier, repository)
        items[key] = (identifier, leaf, context)

    depths = {key: 0 for key in items}
    while True:
        labels = {}
        collisions = defaultdict(list)
        for key, (_, leaf, context) in items.items():
            qualifier = "/".join(reversed(context[:depths[key]]))
            labels[key] = f"{leaf} ({qualifier})" if qualifier else leaf
            collisions[labels[key].casefold()].append(key)
        conflicts = [keys for label, keys in collisions.items() if len(keys) > 1 or label == "unknown"]
        changed = False
        for keys in conflicts:
            for key in keys:
                if depths[key] < len(items[key][2]):
                    depths[key] += 1
                    changed = True
        if not changed:
            break

    used = {"unknown"}
    result = {}
    for key in sorted(items, key=lambda value: (value.casefold(), value)):
        candidate = labels[key]
        if candidate.casefold() in used or len(collisions[candidate.casefold()]) > 1:
            digest = sha256(key.encode("utf-8")).hexdigest()
            length = 6
            candidate = f"{labels[key]} ({digest[:length]})"
            while candidate.casefold() in used:
                length += 1
                candidate = f"{labels[key]} ({digest[:length]})"
        used.add(candidate.casefold())
        result[key] = ProjectLabel(candidate, items[key][0])
    return result
