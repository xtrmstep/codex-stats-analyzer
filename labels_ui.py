"""Manual label management controls."""

from copy import deepcopy

import streamlit as st

from annotations import StorageError
from labels import assign_labels, delete_label, run_labels, upsert_label


def manage(store, snapshot, session_ids):
    """Render label CRUD and bulk assignment; save only after explicit actions."""
    data = snapshot.data
    with st.expander("Manage manual labels"):
        st.caption("Labels are manual classifications, not proof that a skill or agent was used. Runs inherit session labels; explicit run labels are shown separately.")
        definitions = {item["id"]: item for item in data["labels"]}
        options = ["Create new label"] + list(definitions)
        choice = st.selectbox("Label to edit", options, format_func=lambda key: definitions[key]["name"] if key in definitions else key)
        current = definitions.get(choice, {})
        with st.form("label_editor"):
            name = st.text_input("Label name", value=current.get("name", ""))
            key = st.text_input("Structured key (optional)", value=current.get("key", ""))
            value = st.text_input("Structured value (optional)", value=current.get("value", ""))
            save = st.form_submit_button("Save label")
            remove = st.form_submit_button("Delete label", disabled=not current)
        if save or remove:
            updated = deepcopy(data)
            try:
                if remove:
                    delete_label(updated, choice)
                else:
                    upsert_label(updated, name, key, value, choice if current else None)
                store.save(updated, snapshot.revision)
                st.rerun()
            except (ValueError, StorageError) as exc:
                st.error(str(exc))
        runs = {run["id"]: run for run in data["runs"]}
        target_type = st.selectbox("Assign to", ["session", "run"])
        targets = session_ids if target_type == "session" else sorted(runs)
        with st.form("label_assignment"):
            target_ids = st.multiselect("Sessions or runs", targets)
            chosen = st.multiselect("Labels", list(definitions), format_func=lambda item: definitions[item]["name"])
            action = st.radio("Assignment action", ["add", "remove"], horizontal=True)
            apply = st.form_submit_button("Apply to selected")
        if apply:
            updated = deepcopy(data)
            try:
                assign_labels(updated, target_type, target_ids, chosen, action)
                store.save(updated, snapshot.revision)
                st.rerun()
            except (ValueError, StorageError) as exc:
                st.error(str(exc))
        if runs:
            display = []
            for run in runs.values():
                explicit, inherited = run_labels(data, run)
                display.append({"Run": run["name"], "Session": run["session_id"],
                                "Explicit": ", ".join(definitions[x]["name"] for x in sorted(explicit) if x in definitions),
                                "Inherited": ", ".join(definitions[x]["name"] for x in sorted(inherited) if x in definitions)})
            st.dataframe(display, hide_index=True, use_container_width=True)

