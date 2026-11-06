"""Streamlit editor and views for saved comparison definitions."""

from copy import deepcopy
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from annotations import MetadataStore, StorageError
from experiment_store import FILTER_FIELDS, METRICS, groups_from_definition, record_snapshot, upsert_experiment
from experiments import compare_groups


def _serialize_filters(selection, agent, runs):
    values = asdict(selection)
    for key, value in values.items():
        if isinstance(value, (set, frozenset)):
            values[key] = sorted(value)
        elif isinstance(value, date):
            values[key] = value.isoformat()
    values["agent"] = agent
    values["run_ids"] = list(runs)
    return values


def render_experiments(data, events, increments, frame, selection, selected_agent, chosen_runs):
    """Edit, recalculate and explicitly snapshot saved comparisons."""
    store = MetadataStore(Path(__file__).resolve().parent / "data" / "experiments.json", "experiments")
    try:
        snapshot = store.load()
    except StorageError as exc:
        st.error(f"Saved experiments unavailable: {exc}")
        return
    with st.expander("Experiment comparison"):
        st.caption("Groups intersect the current global filters. The first group is the baseline. Results are descriptive and do not establish causation.")
        saved = {item["id"]: item for item in snapshot.data["experiments"]}
        choice = st.selectbox("Experiment", ["New experiment"] + list(saved), format_func=lambda key: saved[key]["name"] if key in saved else key)
        current = saved.get(choice, {})
        editor_key = f"experiment_editor_{choice}"
        name = st.text_input("Experiment name", value=current.get("name", ""), key=f"{editor_key}_name")
        existing = current.get("groups", [])
        count = st.number_input("Number of groups", min_value=2, max_value=20, value=max(2, min(20, len(existing) or 2)), step=1, key=f"{editor_key}_count")
        definitions = {item["id"]: item["name"] for item in data["labels"]}
        available = {
            "label_ids": list(definitions),
            "task_types": sorted({run.get("task_type") for run in data["runs"] if run.get("task_type")} | {label["value"] for label in data["labels"] if label.get("key", "").casefold() == "task_type" and label.get("value")}),
            "execution_modes": sorted({run.get("execution_mode") for run in data["runs"] if run.get("execution_mode")} | {label["value"] for label in data["labels"] if label.get("key", "").casefold() == "execution_mode" and label.get("value")}),
            "projects": sorted(frame["project"].dropna().unique().tolist()),
            "models": sorted(frame["model"].dropna().unique().tolist()),
            "sessions": sorted({run["session_id"] for run in data["runs"]}),
            "agent_roles": sorted(frame["agent_role"].dropna().unique().tolist()),
        }
        groups = []
        unsupported_metrics = [metric for metric in current.get("metrics", []) if metric not in METRICS]
        if unsupported_metrics:
            st.warning("Unsupported saved metrics will be removed if this definition is saved: " + ", ".join(unsupported_metrics))
        with st.form(editor_key):
            for index in range(int(count)):
                old = existing[index] if index < len(existing) else {}
                old_filters = old.get("filters", {})
                st.write(f"Group {index + 1}")
                group_name = st.text_input("Group name", value=old.get("name", f"Group {index + 1}"), key=f"{editor_key}_group_{index}_name")
                filters = {}
                for field in FILTER_FIELDS:
                    prior = old_filters.get(field) or []
                    options = sorted(set(available[field]) | set(prior))
                    labels = {"label_ids": "Labels", "task_types": "Task types", "execution_modes": "Execution modes", "projects": "Projects", "models": "Models", "sessions": "Sessions", "agent_roles": "Agent roles"}
                    selected = st.multiselect(labels[field], options, default=prior, key=f"{editor_key}_group_{index}_{field}", format_func=(lambda value: definitions.get(value, f"Missing label: {value}")) if field == "label_ids" else str)
                    filters[field] = selected or None
                modes = ["all", "any"]
                filters["label_mode"] = st.selectbox("Match labels", modes, index=modes.index(old_filters.get("label_mode", "all")), key=f"{editor_key}_group_{index}_mode")
                groups.append({"name": group_name, "filters": filters})
            metrics = st.multiselect("Comparison metrics", list(METRICS), default=[metric for metric in current.get("metrics", []) if metric in METRICS] if current else ["mean_tokens", "median_tokens", "elapsed_seconds"], key=f"{editor_key}_metrics")
            save = st.form_submit_button("Save experiment")
            delete = st.form_submit_button("Delete experiment", disabled=not current)
        candidate = dict(current)
        candidate.update(name=name, groups=groups, metrics=metrics)
        if save or delete:
            updated = deepcopy(snapshot.data)
            try:
                if delete:
                    updated["experiments"] = [item for item in updated["experiments"] if item["id"] != choice]
                else:
                    upsert_experiment(updated, candidate)
                store.save(updated, snapshot.revision)
                st.rerun()
            except (ValueError, StorageError) as exc:
                st.error(str(exc))
        try:
            comparison = compare_groups(groups_from_definition(candidate), data, events, increments, frame, selection)
        except (KeyError, ValueError) as exc:
            st.info(f"Complete the comparison definition: {exc}")
            return
        if chosen_runs:
            filtered_data = deepcopy(data)
            filtered_data["runs"] = [run for run in data["runs"] if run["id"] in chosen_runs]
            comparison = compare_groups(groups_from_definition(candidate), filtered_data, events, increments, frame, selection)
        table = []
        for group in comparison.groups:
            for metric in metrics:
                measure = group.measures[metric]
                diff = comparison.differences.get(group.name, {}).get(metric)
                table.append({"Group": group.name, "Runs": len(group.run_ids), "Metric": metric, "Value": measure.value,
                              "Eligible": measure.eligible, "Total": measure.total, "Provenance": measure.provenance,
                              "Difference from baseline": diff.absolute if diff else None,
                              "Difference %": diff.percentage if diff else None})
        st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
        for metric in metrics:
            chart = pd.DataFrame([row for row in table if row["Metric"] == metric])
            if not chart.empty and chart["Value"].notna().any():
                st.plotly_chart(px.bar(chart, x="Group", y="Value", color="Group", title=metric, hover_data=["Runs", "Eligible", "Total", "Provenance"]), use_container_width=True)
        distribution = [{"Group": group.name, "Run ID": run, "Tokens": value} for group in comparison.groups for run, value in group.distribution]
        if distribution:
            st.plotly_chart(px.box(pd.DataFrame(distribution), x="Group", y="Tokens", points="all", hover_data=["Run ID"], title="Root-thread token distribution"), use_container_width=True)
        for caveat in (*comparison.caveats, *comparison.condition_flags):
            st.warning(caveat)
        for pair, run_ids in comparison.overlapping_runs.items():
            st.warning(f"Groups {pair} share {len(run_ids)} run(s): {', '.join(run_ids)}")
        if current:
            st.caption("History contains only explicitly recorded calculations, including their global filters. Editing groups or metrics clears previous history. Current results recalculate independently.")
            definition_changed = current.get("groups") != groups or current.get("metrics") != metrics
            if definition_changed:
                st.info("Save group or metric changes before recording a history point.")
            if st.button("Record current calculation", disabled=definition_changed):
                updated = deepcopy(snapshot.data)
                try:
                    item = next(item for item in updated["experiments"] if item["id"] == choice)
                    saved_comparison = compare_groups(groups_from_definition(item), data if not chosen_runs else filtered_data, events, increments, frame, selection)
                    record_snapshot(item, saved_comparison, _serialize_filters(selection, selected_agent, chosen_runs))
                    store.save(updated, snapshot.revision)
                    st.rerun()
                except (ValueError, StorageError) as exc:
                    st.error(str(exc))
            history = [{"Recorded at": snap["recorded_at"], "Group": group["name"], "Metric": metric, "Value": value["value"], "Eligible": value["eligible"], "Runs": group["run_count"]}
                       for snap in current.get("history", []) for group in snap["groups"] for metric, value in group["measures"].items()]
            if history:
                st.dataframe(pd.DataFrame(history), hide_index=True, use_container_width=True)
                st.write("Recorded global filter contexts", [{"recorded_at": snap["recorded_at"], "filters": snap["global_filters"]} for snap in current["history"]])
                history_metric = st.selectbox("History metric", metrics, key=f"{editor_key}_history_metric") if metrics else None
                filtered = pd.DataFrame([row for row in history if row["Metric"] == history_metric])
                if not filtered.empty and filtered["Value"].notna().any():
                    st.plotly_chart(px.line(filtered, x="Recorded at", y="Value", color="Group", markers=True, hover_data=["Eligible", "Runs"], title="Recorded calculation history"), use_container_width=True)
                st.caption("Recorded points may use different global filters; inspect the saved snapshot context before comparing them.")



