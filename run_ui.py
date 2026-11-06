"""Run editor and table helpers."""

from copy import deepcopy
import statistics

import pandas as pd
import streamlit as st

from annotations import StorageError
from labels import assign_labels, assigned, matches, run_labels
from metrics import summarize
from runs import calculate_run, delete_run, upsert_run


def select_runs(data, events, increments, selection, base):
    """Select runs by manual classification and intersect usage with base filters."""
    matches_list = []
    for run in data["runs"]:
        explicit, inherited = run_labels(data, run)
        if not matches(data, explicit | inherited, selection.label_ids, selection.label_mode,
                       selection.task_types, selection.execution_modes, run):
            continue
        if selection.sessions is not None and run["session_id"] not in selection.sessions:
            continue
        result = calculate_run(run, events, increments)
        refs = set(result.event_references) | {item.reference for item in result.increments}
        subset = base.loc[(base["session"] == run["session_id"]) & base["reference"].isin(refs)].copy()
        if not subset.empty:
            subset.attrs["manual_filter"] = True
            subset.attrs["run_filter"] = True
            matches_list.append((run, result, subset))

    return matches_list


def run_summary(matches_list, events, data=None):
    """Summarize each run independently, preserving unknown values."""
    rows = []
    for run, result, frame in matches_list:
        total = summarize(frame, events).totals["total_tokens"]
        explicit, inherited = run_labels(data, run) if data is not None else (set(), set())
        names = {item["id"]: item["name"] for item in data["labels"]} if data is not None else {}
        rows.append({"Explicit labels": ", ".join(names[x] for x in sorted(explicit) if x in names),
                     "Inherited labels": ", ".join(names[x] for x in sorted(inherited) if x in names),
                     "Run": run["name"], "Run ID": run["id"], "Session": run["session_id"],
                     "Tokens": total.value, "Coverage": "Partial or unknown", "Attribution": result.attribution + "; root thread only",
                     "Outcome": run.get("outcome", "unknown"), "Task type": run.get("task_type", ""),
                     "Full run elapsed seconds": result.elapsed_seconds, "Elapsed provenance": result.elapsed_provenance,
                     "Diagnostics": "; ".join(result.diagnostics)})
    known = [row["Tokens"] for row in rows if row["Tokens"] is not None]
    return rows, (statistics.mean(known) if known else None), (statistics.median(known) if known else None)


def manage_runs(store, snapshot, events, increments):
    """Render run editor with explicit save, deletion and label assignment."""
    data = snapshot.data
    runs = {run["id"]: run for run in data["runs"]}
    sessions = sorted({event.session_id for event in events} | {run["session_id"] for run in runs.values()})
    with st.expander("Manage runs"):
        st.caption("Runs cover the selected root thread only; child usage is excluded. Interval token attribution is estimated.")
        choice = st.selectbox("Run to edit", ["Create new run"] + list(runs), format_func=lambda key: runs[key]["name"] if key in runs else key)
        current = runs.get(choice, {})
        if not sessions:
            st.info("A discovered session is needed to create a run.")
            return
        default_session = sessions.index(current["session_id"]) if current.get("session_id") in sessions else 0
        session = st.selectbox("Run session", sessions, index=default_session)
        old_boundary = current.get("boundary", {"type": "whole_session"})
        modes = ["whole_session", "timestamps", "events"]
        mode = st.selectbox("Boundary type", modes, index=modes.index(old_boundary.get("type")) if old_boundary.get("type") in modes else 0)
        event_list = [event for event in events if event.session_id == session]
        event_refs = [event.reference for event in event_list]
        event_text = {event.reference: f"{event.timestamp or 'Unknown time'} — {event.event_type} — {event.reference}" for event in event_list}
        definitions = {label["id"]: label["name"] for label in data["labels"]}
        with st.form("run_editor"):
            name = st.text_input("Run name", value=current.get("name", ""))
            description = st.text_area("Description", value=current.get("description") or "")
            if mode == "timestamps":
                start = st.text_input("Start timestamp (inclusive, with timezone)", value=old_boundary.get("start", ""))
                end = st.text_input("End timestamp (exclusive, with timezone)", value=old_boundary.get("end", ""))
                boundary = {"type": mode, "start": start, "end": end}
            elif mode == "events":
                options = [""] + event_refs
                first = st.selectbox("Start event (inclusive)", options, index=options.index(old_boundary.get("start_event")) if old_boundary.get("start_event") in options else 0, format_func=lambda ref: event_text.get(ref, "Select an event"))
                last = st.selectbox("End event (exclusive)", options, index=options.index(old_boundary.get("end_event")) if old_boundary.get("end_event") in options else 0, format_func=lambda ref: event_text.get(ref, "Select an event"))
                boundary = {"type": mode, "start_event": first, "end_event": last}
            else:
                boundary = {"type": mode}
            task_id = st.text_input("Task identifier", value=current.get("task_id") or "")
            task_type = st.text_input("Task type", value=current.get("task_type") or "")
            execution_mode = st.text_input("Execution mode", value=current.get("execution_mode") or "")
            outcomes = ["unknown", "success", "failure", "partial"]
            outcome = st.selectbox("Outcome", outcomes, index=outcomes.index(current.get("outcome", "unknown")))
            score = st.text_input("Evaluation score (optional number)", value=str(current["evaluation_score"]) if current.get("evaluation_score") is not None else "")
            notes = st.text_area("Notes", value=current.get("notes") or "")
            explicit = assigned(data, "run", choice) if current else set()
            labels = st.multiselect("Explicit run labels", list(definitions), default=sorted(explicit), format_func=lambda label: definitions[label])
            save = st.form_submit_button("Save run")
            remove = st.form_submit_button("Delete run", disabled=not current)
        if save or remove:
            updated = deepcopy(data)
            try:
                if remove:
                    delete_run(updated, choice)
                else:
                    run = dict(current)
                    run.update(name=name, session_id=session, boundary=boundary, description=description,
                               task_id=task_id, task_type=task_type, execution_mode=execution_mode,
                               outcome=outcome, evaluation_score=float(score) if score.strip() else None, notes=notes)
                    run.pop("boundaries", None)
                    identifier = upsert_run(updated, run)
                    current_labels = assigned(updated, "run", identifier)
                    if current_labels:
                        assign_labels(updated, "run", [identifier], current_labels, "remove")
                    if labels:
                        assign_labels(updated, "run", [identifier], labels, "add")
                    result = calculate_run(next(item for item in updated["runs"] if item["id"] == identifier), events, increments)
                    if any("outside observed" in issue or "Boundary event is missing" in issue or "must be in source order" in issue for issue in result.diagnostics):
                        raise ValueError("; ".join(result.diagnostics))
                store.save(updated, snapshot.revision)
                st.rerun()
            except (ValueError, StorageError) as exc:
                st.error(str(exc))





