# 12 — Saved experiments and comparative visualizations

Status: Not started | Phase: 3 | Dependencies: 07, 10, 11

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
