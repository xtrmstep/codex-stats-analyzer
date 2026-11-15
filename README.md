# Codex Usage Analyzer

A local Windows dashboard for inspecting Codex token counters and agent activity. It reads JSONL session files without modifying them. No Codex account or API credentials are required.

## Setup and start

Install Python 3.12 for Windows with the Python launcher, then run `setup.bat`. It creates a project-local `.venv` and installs Streamlit, pandas and Plotly. Run `run.bat` from any working directory, including a path containing spaces. The dashboard listens at [http://localhost:8501](http://localhost:8501), binds to localhost, and disables Streamlit usage telemetry and its email prompt.

The entry point is `src/app.py`. The `src/internal/` packages contain ingestion, analytics, metadata and dashboard code. Configuration and local data remain in the repository root.

For installation without network access, first prepare compatible Python 3.12 Windows wheels, including transitive dependencies, on a connected machine with the same target architecture:

```bat
py -3.12 -m pip download --only-binary=:all: -r requirements.txt -d wheelhouse
```

Transfer the wheelhouse to the target machine and run `setup.bat "C:\path to\wheelhouse"`. Setup uses `--no-index` and installs only from that directory. Runtime is designed for local use.

## Sources and refresh

`config.toml` lists source directories under `[sources].directories`; the defaults are `%USERPROFILE%\.codex\sessions` and `%USERPROFILE%\.codex\archived_sessions`. Add directories as TOML literal strings. Windows `%VARIABLE%` references are expanded and relative paths resolve from the project directory. Missing directories are reported. Run `.venv\Scripts\python.exe src\app.py --check-config` to check the configuration.

Use **Incremental refresh** to collect new source data while retaining previously imported history. Use **Full refresh from source** to replace imported history with the records currently available in the configured folders; saved markers and agent names are kept. Both actions scan all configured source folders, while Overview filters only limit the displayed results. Parsing diagnostics include malformed and incomplete lines. Session/event references generally survive appends and archive moves; files with no session ID use their filename as a fallback, so renaming them changes that identity.

Token totals use independently attributable per-response usage in `token_usage_record`; cumulative and rollup counters are not counted. Session metadata, turn context, and response items provide attribution and timing context. Explicit nested `source.subagent.thread_spawn` metadata and correlated `spawn_agent` tool results can provide relationships. Only supported explicit skill events are treated as skill evidence; ordinary conversation mentions are not. Unknown event shapes and unresolved links remain visible as diagnostics or unknown values. Not all Codex event variants are supported.

## Filters and exports

Overview filters intersect across recorded date, project, model, role and agent. Date ranges use inclusive recorded calendar days; time buckets use recorded clock labels, with weeks starting Monday. Session and thread identities remain internal to attribution and traceability. Missing fields are excluded when their dimension is filtered.

Download the displayed usage report as CSV. Files use UTF-8 with BOM, standard CSV quoting, blank unknown values and recorded ISO 8601 timestamps with their offsets where provided. Coverage identifies partial and estimated values.

## Local data and recovery

`data/codex_usage.sqlite3` stores imported records, saved time markers, and assigned agent names. Back up the database while the application is stopped to preserve them. Historical `data/annotations.json` and `data/experiments.json` files from retired views are left on disk but are no longer used by the dashboard. Original Codex source files are never used for annotation storage.


