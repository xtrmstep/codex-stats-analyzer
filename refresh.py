"""Read-only source fingerprinting for explicit refresh diagnostics."""

import hashlib
from pathlib import Path

from parser import discover_files


def source_manifest(roots: list[Path]):
    """Capture paths and content digests; report files that cannot be read."""
    diagnostics = []
    manifest = {}
    for path in discover_files(roots, diagnostics):
        try:
            digest = hashlib.sha256()
            with path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
            manifest[str(path)] = digest.hexdigest()
        except OSError as exc:
            diagnostics.append(f"Cannot fingerprint {path}: {exc}")
    return manifest, diagnostics


def changes(previous: dict[str, str], current: dict[str, str]):
    """Report new, changed and missing paths without assuming a move."""
    return {"new": sorted(current.keys() - previous.keys()),
            "changed": sorted(path for path in current.keys() & previous.keys() if current[path] != previous[path]),
            "missing": sorted(previous.keys() - current.keys())}
