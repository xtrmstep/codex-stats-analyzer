# 08 — Labels, bulk assignment and classification filters

Status: Not started | Phase: 2 | Dependencies: 05, 07

Specification: §§2.4, 5.1, 6.1; MVP 5, 7, 9.

## Scope

- Support arbitrary free-form tags and structured key/value labels, including the example execution mode, skills, workflow, task type, configuration and result categories.
- Create, edit and delete labels; assign multiple labels to sessions and runs, including bulk assignment to selected records.
- Define rename/delete behavior, duplicate handling, AND/OR filter composition, and whether session labels are inherited by runs. Display any inherited versus explicit assignment clearly.
- Integrate label combinations, task type and execution mode with shared filters; reconcile structured labels with run metadata fields using a documented rule.
- Treat user classifications as manual metadata, never as automatically detected usage evidence.

## Acceptance and validation

- Verify CRUD, bulk actions, persistence and filter combinations against known assignments.
- Renaming/deleting labels leaves no invalid references; session/run inheritance follows the documented policy.
- Runs created in task 09 can use the same assignment and filtering functions.
