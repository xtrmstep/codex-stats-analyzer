# 12 — Saved experiments and comparative visualizations

Status: Implementation complete; independent review pending | Phase: 3 | Dependencies: 07, 10, 11

Specification: §§7.1–7.4; MVP 8, 9, 13.

## Scope

- Build a comparison editor for two or more groups, label/filter definitions, selected metrics and experiment name.
- Provide a comparison table, grouped aggregate bar charts, token-consumption box plots and experiment-history trend charts.
- Define history semantics explicitly (for example, dated recalculation snapshots stored with experiments); distinguish history from the currently recalculated result.
- Show group sizes, missing-data coverage, absolute/percentage differences, and condition-mismatch flags beside comparisons.
- Save, reopen, edit and delete comparison configurations in `experiments.json`; recalculate saved definitions as runs or annotations change.

## Acceptance and validation

- Save and reopen a three-group comparison; definitions and selected metrics survive restart.
- Adding an eligible run updates recalculated metrics; history follows the documented semantics.
- Verify all chart types, sparse/empty groups and mismatch messages against task 11 results, fully offline.

## Decisions and validation evidence

- Named comparison definitions store two or more groups, label/classification and observed-dimension filters, selected metrics and stable ID in the existing versioned experiment store. Current results are recalculated using task 11 and intersect the dashboard's global filters, selected agent and selected runs. Tables show run counts, metric eligibility/provenance and baseline differences; grouped bars, token box plots and condition/overlap/cause caveats are displayed.
- History records only explicit user snapshots with UTC timestamp, global filter/agent/run context, group sizes, selected values and eligible counts. Recalculation alone does not write history; editing group or metric definitions clears history to avoid mixing definitions. Snapshot contexts are displayed alongside history; trend points may reflect different global filters. History is validated on read/write, while legacy definitions without history remain valid.
- Inline synthetic checks passed three-group save/reopen, preserved metrics, recalculation after adding an eligible run, independent explicit history, and Streamlit-stub construction of Plotly bars, box plot and history trend with an empty group. Modules compiled. Real browser/offline interaction remains unverified; independent review pending.

- Review fixes: stateful widget simulation confirmed saved experiments retain separate editor values when switching; history validation now requires an explicit measure value, permits null, and rejects malformed files without overwriting them. A null history value rendered with a Streamlit stub; compilation passed. Independent re-review pending.
