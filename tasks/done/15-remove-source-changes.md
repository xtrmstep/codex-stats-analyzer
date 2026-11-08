## Title

Remove source change tracking from Codex Usage Analyzer

## Goal

Remove the Source changes feature and its unnecessary file fingerprinting logic while preserving session refresh, parsing diagnostics, and all existing analytics functionality.

## Work

Remove the source change tracking functionality from the application, including its UI, in-memory state, and supporting code.

Review the latest repository state before making changes. The following references describe the current implementation.

### 1. Dashboard — `dashboard.py`

Remove the import:

```python
from refresh import source_manifest, changes
```

Remove the fingerprinting and comparison logic currently located around lines 53–60, including references to:

- `source_manifest`
- `source_changes`
- `fingerprint_diagnostics`
- `changes(previous, manifest)`

Remove the Source changes expander, change-count notification, and fingerprint-specific warnings around lines 73–81.

Preserve the existing refresh button and session ingestion:

```python
refresh_requested = st.sidebar.button("Refresh sources")
parsed = ingest(sources)
```

Streamlit already reruns the application when the button is clicked. `ingest(sources)` reads the configured session files without relying on source fingerprints.

### 2. Source fingerprinting — `refresh.py`

The module currently contains two functions:

- `source_manifest()` — calculates SHA-256 hashes of source files.
- `changes()` — compares previous and current manifests.

Remove the module if no other functionality depends on it.

Do not modify the SHA-256 logic in `parser.py`. Those hashes are used for stable event references and duplicate handling, which are unrelated to source change tracking.

### 3. Documentation — `README.md`

Update the *Sources and refresh* section to remove references to detecting and reporting new, changed, moved, or missing files through fingerprint comparison.

Keep documentation describing source refresh, parsing diagnostics, and preservation of saved metadata.

The completed task `tasks/13-refresh-export.md` contains historical implementation notes and should remain unchanged.

The authoritative specification already requires refresh without explicitly requiring fingerprint-based change tracking.

### 4. Scope boundaries

Do not modify:

- Session discovery and parsing.
- Token calculations and accounting.
- Agent and subagent analytics.
- Labels, annotations, and run management.
- Experiment calculations and persistence.
- Parsing diagnostics for missing, unreadable, or malformed source files.
- Stable event references and duplicate detection.

Avoid unrelated refactoring or introducing new functionality.

## Acceptance Criteria

- The Source changes section is no longer displayed.
- New, changed, and missing file counts are no longer displayed.
- Source fingerprint generation and comparison have been removed.
- No unused imports, functions, or Streamlit state keys related to source change tracking remain.
- `refresh.py` is removed if it has no remaining dependencies.
- The Refresh sources button remains available and triggers fresh ingestion.
- Session discovery and token calculations continue to use the existing parser.
- Parsing and accounting diagnostics remain available.
- Stable event reference hashing in `parser.py` is unchanged.
- Existing labels, runs, annotations, and saved experiments are unaffected.
- `README.md` accurately reflects the remaining refresh behavior.
- Existing project checks and relevant tests, if available, pass. No new test framework or end-to-end test suite is required.
