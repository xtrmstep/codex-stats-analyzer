# AGENTS Instructions Template (AGENTS.md)

<!--
This file is the authoritative guide for AI agents and developers working in this repo.
Keep it accurate and up to date as the project evolves.

Maintenance rules:
- Be conceptual: describe purpose and boundaries, not internal implementation.
- Update this file only when a new layer, naming rule, or workflow change is explicitly defined and requested.
- Do not paste SQL here. Reference file paths instead.
- Sections must stay in the order defined below.
- Do not update this file for code changes or during task execution unless explicitly requested.
-->

## Agent collaboration

Use subagents whenever independent parts of a task can be executed in parallel and doing so would improve speed or quality.

- Delegate independent work automatically without asking for confirmation.
- Avoid assigning multiple agents to modify the same files.
- As the main agent, coordinate execution, wait for subagents to finish, review their changes, and validate the final result.
- For simple or sequential tasks, work directly without spawning subagents.
- Prefer independent reviewer agents for code reviews.
- Do not create unnecessary agents or delegation layers.
- Subagents must not delegate further unless explicitly authorized.

### Agent roles and models

| Role | Model | Responsibility |
|---|---|---|
| Orchestrator | Current session model | Task coordination, delegation, commits, and progress |
| Developer | Terra | Implementation and bug fixing |
| Code Reviewer | Astra | Independent review against tasks and specifications |
| Specification Writer | Astra | Specification creation and modification |
| Lightweight Helper | Luna | Small, independent, low-complexity activities |

### Model enforcement

- Explicitly select the configured model when creating each subagent.
- Never rely on automatic or default model selection for subagents.
- Never substitute a configured model without explicit user approval.
- Use the exact supported model identifier corresponding to each configured model.
- If a required model is unavailable or cannot be explicitly selected, stop the affected task and report the limitation.
- Do not delegate work to agents using unconfigured models.
- The orchestrator remains responsible for the final result, regardless of delegation.

### Role boundaries

- The Developer implements code changes and addresses review findings.
- The Code Reviewer independently inspects actual changes and reports issues. It must not approve work based only on the developer's summary.
- The Specification Writer modifies specifications only when explicitly required by the current task.
- The Lightweight Helper handles small independent activities and does not modify production code.
- The Orchestrator manages task sequencing, Git operations, and review completion.

## Git workflow

### Default branch discovery

- Always use the repository's actual default branch. Never assume or hardcode its name.
- Determine the default branch from the remote repository before starting Git operations.
- Use `git symbolic-ref refs/remotes/origin/HEAD` to identify the locally known remote default branch.
- If that reference is unavailable or outdated, use `git ls-remote --symref origin HEAD` to identify the remote's current default branch.
- Fetch the latest remote changes before creating a task branch.
- If the default branch cannot be determined reliably, stop and report the problem.

### Branches and commits

- For every new task, create a separate task branch from the latest remote default branch before making changes.
- Make all changes on the task branch, never directly on the default branch.
- Continue follow-up iterations for the same task on that task branch.
- After each completed iteration, perform appropriate static checks, create a descriptive commit, and push the task branch.
- Set the upstream on the first push.
- Keep each iteration as a separate commit; do not amend or squash earlier iterations unless explicitly requested.
- Treat committing and pushing each iteration as part of the requested work without requiring additional confirmation.
- If a commit or push is blocked, report the blocker and what remains uncommitted or unpushed.

### Commit conventions

- Create one implementation commit per completed task.
- Create additional commits for subsequent bug fixes identified during review.
- Keep each commit limited to one logical change.
- Use short, compact, non-technical commit messages.
- Prefix each message with a slug identifying the task.
- Do not amend or squash commits unless explicitly requested.

Format:

`<task-slug>: <short description>`

Examples:

- `data-import: add file import`
- `data-import: fix missing records`
- `dashboard: add date filtering`

### Shortcut: merge the working branch to the default branch

When the user says "bring latest to main", "merge work to main", "merge to default branch", or a similar command, treat it as authorization to perform the workflow below, including pushing the default branch and deleting the working branch after success.

The working branch is the current task branch where the work was done. The default branch must be discovered from the remote repository. Upstream means each branch's configured remote and corresponding branch.

1. Remember the working branch name. Ensure all pending task changes are committed, checked, and pushed before switching branches.
2. Discover the repository's default branch and switch to it, creating a local tracking branch if needed.
3. Pull the default branch from its upstream using fast-forward only. If the pull fails, stop and report the reason.
4. Merge the working branch into the default branch using `git merge --ff-only`. Do not create a merge commit, rebase, or force an update.
5. If the merge succeeds, push the default branch to its upstream.
6. Only after that push succeeds, delete the working branch remotely and locally.
7. If pushing or cleanup fails, report what succeeded and preserve branches not yet deleted.
8. If the merge cannot fast-forward, explain the divergence, preserve both branches, and do not push or delete anything. Abort any active merge if necessary. Do not resolve conflicts automatically.

## 1. Repo structure

<!--
Describe the repository structure at a high level.
Help agents locate relevant files without unnecessary repository-wide scanning.
-->

- `specification/` contains the authoritative product specification.
- `tasks/README.md` contains the ordered task plan and dependencies; the numbered files contain individual task descriptions.
- The application has not yet been implemented. Consult the specification and task plan for its intended structure.

## 2. Naming conventions

- Follow PEP 8 conventions for Python code.
- Use descriptive names that clearly communicate intent.
- Use `snake_case` for modules, functions, methods, and variables.
- Use `PascalCase` for classes.
- Use `UPPER_SNAKE_CASE` for constants.
- Avoid unnecessary abbreviations and redundant names.
- Preserve existing project-specific naming conventions.

<!--
Add any additional project-specific naming rules here.
-->

## 3. Documentation and tests policy

### Documentation

- Use Google-style docstrings for Python classes and methods.
- Describe purpose, parameters, return values, and exceptions where applicable.
- Keep docstrings concise and avoid repeating information obvious from names or type hints.
- Add inline comments only when necessary to explain **why** something is implemented in a particular way.
- Document non-obvious decisions, constraints, and workarounds.
- Avoid comments that merely describe what the code does.
- Keep documentation consistent with implementation changes.

### Tests and validation

- Use agent-performed static analysis and code inspection as the primary validation method.
- Check changes against task requirements, specifications, and existing architecture.
- Inspect for logical errors, missing requirements, incorrect dependencies, and unintended changes.
- Do not create or modify unit tests unless explicitly requested.
- Do not introduce testing frameworks or additional testing infrastructure.
- Existing project tests and static analysis tools may be executed when available and relevant.
- Verify modified code imports and executes correctly when applicable.
- Do not require new automated tests for task completion.
- Do not claim successful validation without performing the relevant checks.

### Specification protection

- Treat specifications as authoritative requirements.
- Do not modify specifications unless explicitly required by the current task.
- Do not modify specifications to justify implementation differences.
- If implementation and specifications disagree, correct the implementation or report the conflict.
- Do not update `AGENTS.md` during ordinary task execution.

## 4. How-to

### Python implementation

#### General principles

- Follow existing project conventions, architecture, and specifications.
- Prefer simple, readable, and maintainable solutions.
- Apply low coupling and high cohesion.
- Follow the single responsibility principle.
- Prefer explicit, straightforward code over clever implementations.
- Avoid overengineering, unnecessary abstractions, and speculative functionality.
- Avoid code duplication, but do not introduce abstractions for trivial or isolated cases.

#### Code organization

- Organize code into modules with clear responsibilities.
- Use classes to encapsulate related state and behavior.
- Keep classes focused and reasonably small.
- Prefer composition over inheritance.
- Use constructor-based dependency injection where appropriate.
- Minimize dependencies between modules and classes.
- Keep implementation details private unless external access is required.
- Do not introduce interfaces, base classes, factories, or design patterns without a concrete need.

#### Changes and refactoring

- Make the smallest necessary changes to satisfy the task.
- Preserve existing behavior unless explicitly required otherwise.
- Do not refactor unrelated code.
- Do not introduce new dependencies unless necessary.
- Reuse existing components and utilities where appropriate.
- Avoid changing public interfaces unless required.
- Remove obsolete code introduced by the current change, but avoid unrelated cleanup.
- Modify only files relevant to the task.

### Sequential task execution

When instructed to execute tasks from the `tasks/` folder, follow this workflow.

#### 1. Preparation

- Identify tasks and execute them sequentially in their defined order.
- Before starting each task, read its description, relevant specifications, and existing implementation.
- Inspect only relevant parts of the repository.
- Identify dependencies and requirements before implementation.
- Create the task branch from the latest remote default branch according to the Git workflow.
- Do not start the next task until the current task passes review.

#### 2. Implementation

- Assign implementation to the configured Developer model.
- Consider delegating independent supporting activities to subagents when beneficial.
- Follow project architecture, coding conventions, and specifications.
- Implement only what the task requires.
- Avoid unrelated changes or speculative improvements.
- Perform static validation after implementation.
- Existing tests may be executed when relevant.
- Create one implementation commit and push it.

#### 3. Code review

After implementation is committed:

1. Assign an independent review to the configured Code Reviewer model.
2. Review the actual Git diff and relevant implementation.
3. Compare changes against the task description and applicable specifications.
4. Check correctness, completeness, architectural consistency, and compliance with coding instructions.
5. Identify bugs, missing requirements, unintended changes, and unnecessary complexity.
6. Report review findings clearly, including relevant file locations.

The reviewer must not rely solely on the developer's summary.

#### 4. Bug fixing

When review identifies blocking issues:

1. Assign fixes to the configured Developer model.
2. Make the smallest necessary corrections.
3. Perform static validation of the corrected implementation.
4. Create a separate commit for each logical bug fix and push it.
5. Repeat the independent code review.

Continue until no blocking issues remain.

Do not modify specifications to make incorrect code appear compliant.

#### 5. Task completion

A task is complete only when:

- All requirements are implemented.
- Static validation and code inspection have passed.
- Existing project tests have passed if they were executed.
- Independent code review has passed.
- All required fixes are committed and pushed.
- No blocking issues remain.

Only then proceed to the next task.

For a batch of tasks, preserve the separate-branch-per-task policy. Do not assume changes from an unmerged task branch are present in the next branch. If a subsequent task depends on unmerged work, report the dependency rather than silently changing the branching or merge policy.

#### 6. Autonomous execution

- Execute tasks autonomously only when they are independent and do not require unresolved changes from other task branches.
- Follow the defined task order, completing implementation, commits, and review before moving to the next task.
- Prefer fast-forward-only merges for integrating completed task branches into the default branch.
- Never perform automatic merges unless explicitly authorized by the user or the current task instructions.
- Never use merge commits, rebasing, or force pushes to bypass a failed fast-forward merge.
- If a task depends on unmerged changes, stop and report the dependency.
- Maintain a clear record of completed, active, and remaining tasks.
- Avoid unnecessary communication during normal execution.
- If a task is blocked, report the reason and do not mark it as completed.
- After all tasks are processed, provide a concise summary of completed tasks, commits, review results, and unresolved issues.
- Do not skip required reviews or static validation to accelerate execution.
- Never substitute unavailable models silently.

<!--
Add project-specific how-to instructions below.
For example: adding a service, class, configuration, or data processing component.
-->
