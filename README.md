# Codex Usage Analyzer

A local Windows dashboard for inspecting Codex session activity, token counters, manual labels, runs and comparisons. It reads JSONL session files without modifying them. No Codex account or API credentials are required.

## Setup and start

Install Python 3.12 for Windows with the Python launcher, then run `setup.bat`. It creates a project-local `.venv` and installs Streamlit, pandas and Plotly. Run `run.bat` from any working directory, including a path containing spaces. The dashboard listens at [http://localhost:8501](http://localhost:8501), binds to localhost, and disables Streamlit usage telemetry and its email prompt.

For installation without network access, first prepare compatible Python 3.12 Windows wheels, including transitive dependencies, on a connected machine with the same target architecture:

```bat
py -3.12 -m pip download --only-binary=:all: -r requirements.txt -d wheelhouse
```

Transfer the wheelhouse to the target machine and run `setup.bat "C:\path to\wheelhouse"`. Setup uses `--no-index` and installs only from that directory. Runtime is designed for local use. A synthetic browser workflow including saved runs and comparison history passed across restart with the Python application process restricted to loopback; physical network disconnection and browser-level network blocking have not been verified.

## Sources and refresh

`config.toml` lists source directories under `[sources].directories`; the defaults are `%USERPROFILE%\.codex\sessions` and `%USERPROFILE%\.codex\archived_sessions`. Add directories as TOML literal strings. Windows `%VARIABLE%` references are expanded and relative paths resolve from the project directory. Missing directories are reported. Run `.venv\Scripts\python.exe app.py --check-config` to check the configuration.

Use **Refresh sources** to reread local files and recalculate analytics and saved comparisons. Parsing diagnostics include malformed and incomplete lines. Unavailable annotated sessions and run boundaries are reported without deleting metadata. Session/event references generally survive appends and archive moves; files with no session ID use their filename as a fallback, so renaming them changes that identity.

Supported structures include session metadata, turn context, response items, cumulative `event_msg.token_count` and `token_usage_record` counters. Explicit nested `source.subagent.thread_spawn` metadata and correlated `spawn_agent` tool results can provide relationships. Only supported explicit skill events are treated as skill evidence; ordinary conversation mentions are not. Unknown event shapes and unresolved links remain visible as diagnostics or unknown values. Not all Codex event variants are supported.

## Filters, labels and runs

Filters intersect across UTC date, project, model, session, role, agent, labels, task type, execution mode and runs. Date ranges are inclusive UTC calendar days. Missing fields are excluded when their dimension is filtered. Chart/table groups may overlap, so their values need not add to the global total.

Use **Manage manual labels** to create free-form labels or structured key/value labels and bulk-assign them to sessions and runs. Runs inherit session labels; explicit and inherited labels are shown separately. Label edits preserve assignments; deletion removes the label from assignments. Labels are manual classifications, not evidence that a skill or subagent was used.

Use **Manage runs** to create, edit or delete a run from a session. Choose the whole session, timezone-aware timestamp boundaries, or stable start/end event references. Intervals are start-inclusive and end-exclusive. Whole-session runs expand when new events arrive. Overlapping run selections are deduplicated for global usage, while individual run totals may overlap.

Run calculations include root-thread counters only; child usage is excluded because parent and child counter scopes are not resolved. Interval usage is estimated from counter observation times and may span boundaries. Partial and unknown amounts are labeled; unknown is not zero. Cached input is part of input and reasoning output is part of output, so neither is added twice. Hierarchy spans show first/last recorded activity, not verified execution duration. Main/subagent shares remain unknown where counter overlap cannot be resolved.

## Comparisons and exports

Use **Experiment comparison** to define at least two named groups, choose filters and metrics, then save or reopen the definition. Groups intersect the current global filters; the first group is the baseline. Tables show eligible counts and gaps, group overlaps and differences in recorded conditions. Differences are descriptive, not evidence of causation. Percentage changes are unknown when the baseline is zero or missing. Scores and outcomes are manual; unknown and partial outcomes do not count as failures.

Current comparisons recalculate from the latest source and annotation data. **Record current calculation** adds a timestamped history point with its global filter context; recalculation alone does not add history. Changing a saved group's definition or selected metrics clears that experiment's history. History points with different filter contexts may not be directly comparable.

Download buttons export the displayed filtered session, run and comparison tables as CSV. Files use UTF-8 with BOM, standard CSV quoting, blank unknown values and UTC ISO 8601 timestamps where provided. Column names identify token, percentage and second units; coverage and provenance identify partial and estimated values.

## Local data and recovery

`data/annotations.json` stores labels, assignments and runs. `data/experiments.json` stores comparison definitions and explicit history. These files and `.venv` are excluded from version control. Back up both JSON files while the application is not writing; restore them to `data/` to recover metadata. Original Codex source files are never used for annotation storage.

Writes validate the versioned data, use a same-directory temporary file and atomic replacement, and check for concurrent changes. If a file is corrupt or its schema version is unsupported, preserve it and restore a backup or use a compatible application version; the app will not silently replace it with an empty document. A `.lock` file may remain after interruption: inspect it and remove it only after confirming no writer is active. Cooperating application writers use the lock; unrelated programs can ignore it.


