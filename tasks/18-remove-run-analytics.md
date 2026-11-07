## Title

Remove run management and run-based analytics

## Goal

Simplify Codex Usage Analyzer by removing manually defined runs, their token calculations, and dependent experiment comparisons. Keep automatic session and agent analytics, filtering, and manual session labels.

## Work

### 1. Remove run functionality

Remove run creation, editing, deletion, interval boundaries, and token attribution.

Relevant files:
- `runs.py` — run validation, boundaries, token calculation, and overlap handling.
- `run_ui.py` — run management, selection, and summary calculations.
- `dashboard.py` — run-related UI and analytics integration.

Technical hints — remove these run-specific calls from `dashboard.py`:

```python
manage_runs(...)
run_matches = select_runs(...)
run_rows, run_mean, run_median = run_summary(...)
```

Remove the corresponding imports and any unused code.

### 2. Remove run-related dashboard elements

Remove:
- Runs filter and management interface.
- Runs count, average tokens per run, and median tokens per run.
- Run breakdown option.
- Runs table and CSV export.
- Unavailable run references and run-specific warnings.

Preserve session, project, model, agent, and label analytics.

### 3. Remove dependent experiment comparisons

The current experiment functionality calculates comparisons exclusively from manually defined runs.

Relevant files:
- `experiments.py`
- `experiment_ui.py`
- `experiment_store.py`

Remove run-based experiment calculations, comparison UI, saved comparison management, and history presentation.

Technical hint — `experiments.py` depends directly on:

```python
for run in data["runs"]:
    ...
    result = calculate_run(run, events, increments)
```

Do not introduce session-based experiment comparisons as part of this task.

### 4. Simplify annotations and label handling

Relevant files:
- `annotations.py`
- `labels.py`
- `labels_ui.py`

Remove run definitions, run label assignments, inheritance rules, and run-specific validation.

Preserve session labels, including structured `task_type` and `execution_mode` classifications.

Technical hint — `annotations.py` currently expects:

```python
("labels", "assignments", "runs")
```

`labels.py` also supports two assignment targets:

```python
("session", "run")
```

Existing annotation files may contain run definitions and run assignments. They must remain readable without losing valid session labels. Historical metadata files must not be automatically deleted.

### 5. Simplify filtering and metric calculation

Relevant files:
- `dashboard.py`
- `metrics.py`

Remove run-specific filtering, selection merging, and coverage adjustments.

Technical hint — `metrics.py` already supports session-level manual filtering through:

```python
filter_dataset(frame, selection, annotations)
```

Review the run-specific code path:

```python
if frame.attrs.get("run_filter"):
    totals = {
        name: Total(total.value, False)
        for name, total in totals.items()
    }
```

Remove run-only handling while preserving conservative token accounting, unknown values, and overlap protection for agent streams.

### 6. Clean up exports and documentation

Relevant files:
- `exports.py`
- `README.md`
- `specification/codex-usage-analyzer.md`

Remove obsolete run and experiment export definitions, requirements, descriptions, and examples.

Preserve session CSV export and shared export utilities.

Update the product specification to reflect the revised scope. Existing completed task files may remain as historical records.

Do not modify `AGENTS.md` or unrelated application functionality.

## Acceptance Criteria

- No run creation, editing, deletion, or interval attribution functionality remains.
- Run-related filters, metrics, tables, charts, captions, and CSV exports are removed.
- Run-based experiment comparison functionality and related UI are removed.
- Session and agent token calculations retain their existing behavior.
- Session, project, model, agent, date, and manual label filters remain available.
- Structured task type and execution mode filters continue to work through session labels.
- Manual label management supports sessions without run dependencies.
- Existing annotations containing legacy run data do not prevent valid session labels from loading or being saved.
- Existing annotation and experiment files are not automatically deleted.
- No obsolete imports or runtime dependencies on removed run and experiment modules remain.
- Unused run-specific calculations, data structures, and export definitions are removed.
- README and product specification match the remaining functionality.
- Static code inspection and Python compilation complete without errors.
- No new tests, dependencies, or replacement features are introduced.
