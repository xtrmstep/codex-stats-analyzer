"""Descriptive comparisons of sessions in the published overview dataset."""

from dataclasses import replace
from statistics import mean, median

import pandas as pd
import plotly.express as px
import streamlit as st


def render_session_comparisons(calculator, request, selected):
    """Compare selected session groups under the current Overview filters."""
    st.subheader("Session comparisons")
    st.caption("Groups use the current Overview filters and full selected period. Differences are observations, not causal conclusions.")
    sessions = sorted(selected["session"].dropna().unique().tolist())
    count = int(st.number_input("Number of comparison groups", min_value=2, max_value=20, value=2, step=1))
    groups = []
    for index in range(count):
        name = st.text_input(f"Group {index + 1} name", value=f"Group {index + 1}")
        members = st.multiselect(f"Group {index + 1} sessions", sessions, key=f"comparison_sessions_{index}")
        groups.append((name.strip() or f"Group {index + 1}", frozenset(members)))
    if any(not members for _, members in groups):
        st.info("Select at least one session for each group to compare them.")
        return
    if len({name.casefold() for name, _ in groups}) != len(groups):
        st.warning("Group names must be unique.")
        return

    table = []
    distribution = []
    conditions = []
    for name, members in groups:
        group_request = replace(request, marker=None, sessions=members)
        summary = calculator.calculate(group_request)["Full selected period"][0]
        values = []
        complete = 0
        for session in sorted(members):
            result = calculator.calculate(replace(group_request, sessions=frozenset({session})))["Full selected period"][0]
            value = result.totals["total_tokens"]
            if value is not None:
                values.append(value)
                distribution.append({"Group": name, "Session": session, "Tokens": value, "Coverage": result.coverage})
            complete += result.coverage == "complete"
        table.append({"Group": name, "Sessions": len(members),
                      "Average tokens per session": mean(values) if values else None,
                      "Median tokens per session": median(values) if values else None,
                      "Output tokens": summary.totals["output_tokens"], "Cache %": summary.cache_percentage,
                      "Subagent share %": summary.subagent_share, "Elapsed seconds": None,
                      "Coverage": summary.coverage, "Known token totals": len(values), "Complete sessions": complete})
        model_values = selected.loc[selected["session"].isin(members), "model"]
        models = {str(value) for value in model_values.dropna().unique()}
        if model_values.isna().any() or model_values.empty:
            models.add("Unknown")
        conditions.append(models)

    metrics = ("Average tokens per session", "Median tokens per session", "Output tokens", "Elapsed seconds")
    for row in table:
        for metric in metrics:
            base, value = table[0][metric], row[metric]
            delta = value - base if base is not None and value is not None else None
            row[f"{metric} difference"] = delta
            row[f"{metric} difference %"] = 100 * delta / base if delta is not None and base != 0 else None
    st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
    st.caption("Coverage and known counts indicate partial data. Elapsed duration is unknown when it cannot be verified.")
    for metric in metrics:
        chart = pd.DataFrame([{"Group": row["Group"], "Value": row[metric], "Coverage": row["Coverage"]} for row in table])
        if chart["Value"].notna().any():
            st.plotly_chart(px.bar(chart, x="Group", y="Value", color="Group", hover_data=["Coverage"], title=metric),
                            use_container_width=True, key=f"comparison_bar_{metric}")
    if distribution:
        st.plotly_chart(px.box(pd.DataFrame(distribution), x="Group", y="Tokens", points="all",
                               hover_data=["Session", "Coverage"], title="Tokens per session"),
                        use_container_width=True, key="comparison_distribution")
    if any(models != conditions[0] for models in conditions[1:]):
        st.warning("Groups have different observed models, which can affect comparability: " +
                   "; ".join(f"{groups[index][0]}: {', '.join(sorted(models))}" for index, models in enumerate(conditions)))
    for index, (name, members) in enumerate(groups):
        for other_name, other_members in groups[index + 1:]:
            shared = members & other_members
            if shared:
                st.warning(f"{name} and {other_name} share {len(shared)} session(s).")
