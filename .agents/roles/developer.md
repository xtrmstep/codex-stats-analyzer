## Workflow

Execute pending tasks one after another in numeric order, following the [repository instructions](../../AGENTS.md). For each task, create a task branch, implement and verify the work, record and fix issues, then commit and push. Eventually merge completed work to `main` using the repository merge workflow.

## During execution

Follow the specifications and existing architecture. Consider sub-agents for tiny independent tasks and a stronger model, such as GPT Sol 6.1 High, for difficult tasks, where repository instructions permit.

## Limitations

Do not modify specifications while executing tasks; report gaps or conflicts for separate specification work. Use static inspection for the MVP; full runtime testing and reconciliation come later. Do not add migrations, backward-compatibility work or new services. Consult the authorized analysis chat only for a genuine blocker after independent investigation and committing the current changes. Do not ask it to perform static reviews.