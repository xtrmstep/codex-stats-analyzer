## Title

Organize Python application modules under `src`

## Goal

Move application code into a small package structure while preserving existing behavior, launch settings, and access to local data.

## Work

### Source layout

Move the existing modules into the following locations. Add package initializers and update application imports to use the `internal` package. Keep the existing modules intact apart from the entry point, path and import changes, and the accounting module rename.

```text
src/
├── app.py
└── internal/
    ├── paths.py
    ├── ingestion/
    │   ├── collection.py
    │   ├── parser.py
    │   └── transformations.py
    ├── analytics/
    │   ├── agents.py
    │   ├── metrics.py
    │   ├── token_accounting.py
    │   └── usage_statistics.py
    ├── metadata/
    │   ├── annotations.py
    │   ├── experiment_store.py
    │   ├── experiments.py
    │   ├── labels.py
    │   └── runs.py
    └── ui/
        ├── dashboard.py
        ├── experiment_ui.py
        ├── exports.py
        ├── labels_ui.py
        ├── run_ui.py
        └── statistics_ui.py
```

Rename the current `analytics.py` to `token_accounting.py`. Keep the reader, importer, and database writer together in `collection.py`.

### Launch, configuration, and data

- Keep `run.bat`, `config.toml`, `.streamlit/`, `requirements.txt`, `data/`, and repository documentation at the root.
- Use `internal/paths.py` to resolve the repository root and share it with the modules that locate configuration and data. Keep source directories relative to the repository root where configured that way. Continue using the existing paths for `data/codex_usage.sqlite3`, `data/annotations.json`, and `data/experiments.json`.
- Make `run.bat` resolve paths from its own directory and launch `src/app.py` with the existing local Streamlit settings. Preserve `--check-config`. Update the README and repository structure guidance in `AGENTS.md` to match the new layout.
- Keep dependencies, database schema, and analytics behavior as they are. Setup script changes are outside this task.

## Acceptance Criteria

- Application Python files live in the documented source layout. The relocated modules compile and import in the existing virtual environment without installing the project as a package.
- The configuration check still validates the root `config.toml`, expands Windows environment variables, and resolves relative source directories from the repository root.
- `run.bat` starts the app from the repository root and when invoked from another working directory, including paths with spaces. Streamlit still binds to localhost on port 8501 with telemetry disabled.
- The relocated app opens the existing database and JSON metadata at their original paths and does not create replacement data under `src/`. Smoke-check usage views, time markers, session details, labels, runs, experiments, and CSV export.
- The diff consists of module moves, import and path changes, launch script updates, and the corresponding documentation.
