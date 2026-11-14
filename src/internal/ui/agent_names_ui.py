"""Edit and display user-assigned names for individual executions."""

from collections import Counter

import streamlit as st


def execution_labels(threads):
    """Return readable, distinct display labels keyed by stable execution ID."""
    ordered = sorted(threads, key=lambda row: row["execution_id"])
    bases = {}
    for row in ordered:
        chat = row.get("chat_title") or "Untitled chat"
        agent = row.get("nickname") or row.get("role") or row.get("agent_name") or "Agent"
        bases[row["execution_id"]] = f"{chat} — {agent}"
    counts = Counter(bases.values())
    seen = Counter()
    reserved = set(bases.values())
    used = set()
    labels = {}
    for row in ordered:
        key = row["execution_id"]
        base = bases[key]
        if counts[base] == 1:
            label = base
        else:
            while True:
                seen[base] += 1
                label = f"{base} ({seen[base]})"
                if label not in reserved and label not in used:
                    break
        labels[key] = label
        used.add(label)
    return labels


def agent_name_editor(writer):
    """Set or clear a user name without changing imported execution records."""
    st.subheader("Agent names")
    rows = writer.connection.execute(
        "SELECT t.execution_id, t.chat_title, t.nickname, t.role, t.agent_name, n.name "
        "FROM agent_threads t LEFT JOIN agent_names n ON n.execution_id = t.execution_id"
    ).fetchall()
    threads = [dict(zip(("execution_id", "chat_title", "nickname", "role", "agent_name", "assigned_name"), row))
               for row in rows]
    labels = execution_labels(threads)
    if not labels:
        st.info("No agent executions are available to name.")
        return
    choice = st.selectbox("Agent execution", sorted(labels, key=lambda key: labels[key].casefold()),
                          format_func=labels.get)
    assigned = next(row["assigned_name"] for row in threads if row["execution_id"] == choice) or ""
    with st.form(f"agent_name_{choice}"):
        name = st.text_input("Assigned name", value=assigned)
        save = st.form_submit_button("Save agent name")
        clear = st.form_submit_button("Clear agent name")
    if save or clear:
        name = name.strip() if save else ""
        with writer.transaction():
            if name:
                writer.connection.execute("INSERT INTO agent_names (execution_id, name) VALUES (?, ?) "
                                          "ON CONFLICT(execution_id) DO UPDATE SET name = excluded.name", (choice, name))
            else:
                writer.connection.execute("DELETE FROM agent_names WHERE execution_id = ?", (choice,))
        st.rerun()
