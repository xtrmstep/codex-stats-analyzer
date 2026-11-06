# 08 — Labels, bulk assignment and classification filters

Status: Complete; independent review passed | Phase: 2 | Dependencies: 05, 07

Specification: §§2.4, 5.1, 6.1; MVP 5, 7, 9.

## Scope

Review: independent Astra re-review passed at `3975d64`, including malformed structured-field rejection and legacy compatibility.

- Support arbitrary free-form tags and structured key/value labels, including the example execution mode, skills, workflow, task type, configuration and result categories.
- Create, edit and delete labels; assign multiple labels to sessions and runs, including bulk assignment to selected records.
- Define rename/delete behavior, duplicate handling, AND/OR filter composition, and whether session labels are inherited by runs. Display any inherited versus explicit assignment clearly.
- Integrate label combinations, task type and execution mode with shared filters; reconcile structured labels with run metadata fields using a documented rule.
- Treat user classifications as manual metadata, never as automatically detected usage evidence.

## Acceptance and validation

- Verify CRUD, bulk actions, persistence and filter combinations against known assignments.
- Renaming/deleting labels leaves no invalid references; session/run inheritance follows the documented policy.
- Runs created in task 09 can use the same assignment and filtering functions.

## Decisions and validation evidence

- Labels have stable IDs, a unique case-insensitive name and optional key/value pair; duplicate structured pairs are rejected case-insensitively. Rename preserves assignments; deletion removes the ID from all assignments. Bulk add/remove merges duplicate assignment rows. Runs inherit session labels plus explicit run labels, with each shown separately. Manual classifications are not evidence of skill or agent use.
- Label selections combine as all or any, then intersect with task type, execution mode and all other filters. Structured keys `task_type` and `execution_mode` provide classification. For a run, a non-empty direct metadata value overrides labels for that field; otherwise inherited/explicit structured values apply. The global dashboard filters session assignments only: a run label cannot select a whole session's usage before task 09 interval attribution. Run matching is provided for subsequent run workflows; run-driven global filtering belongs to task 10. No usage is multiplied by labels.
- Inline checks passed label CRUD and duplicate handling, bulk add/remove, persistence, run inheritance and metadata precedence, all/any plus execution mode filtering, and manual provenance. A Streamlit stub rendered management against an empty store without writing. Python compilation passed. Browser interaction remains unverified. Independent review pending.

- Review fix: inline checks confirmed legacy labels omitting key/value round-trip; null, numeric or unpaired structured fields fail validation and remain unchanged on disk. Compilation passed; independent re-review pending.
