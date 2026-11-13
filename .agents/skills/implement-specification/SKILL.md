---
name: implement-specification
description: Implement or modify application code to satisfy existing system specifications, including UI screens, architecture requirements, and interface contracts. Use for coding tasks driven by specifications; not for specification-only edits.
---

# Implement Specification

Implement the intended system described by the target repository. The specification and its engineering guidelines provide the requirements; this skill provides the execution workflow.

## Workflow

1. Read the repository's root `AGENTS.md`, `specification/AGENTS.md`, and applicable engineering and verification guidelines.
2. Locate the requirements relevant to the task. Follow their references to affected screens, design documents, and contracts; avoid loading unrelated specifications.
3. Inspect only the relevant code, interfaces, dependencies, and existing tests. Compare current behavior with the specification.
4. Identify the smallest implementation change that satisfies the requirements while preserving unrelated behavior. Follow existing code conventions and applicable architectural constraints.
5. Implement without speculative abstractions, unrelated refactoring, or silent API changes. Keep related contracts consistent.
6. Run applicable syntax, formatting, linting, static, and type checks when available. Perform focused runtime or integration checks when necessary and feasible. Review the changes against the specification, including LLM-assisted analysis when available.
7. Report changed files, verification results, unverified behavior, unresolved requirements, and remaining differences from the specification.

## Boundaries

- Do not modify specifications unless the task explicitly requests specification changes.
- If the specification is missing, incomplete, or contradictory, report the gap rather than inventing required behavior. Continue only with independently clear, authorized work.
- Do not add new unit tests or test infrastructure unless requested or required by the target repository's explicit instructions. Preserve existing tests; run relevant ones where available.
- Do not claim that static checks or an LLM review prove runtime correctness.
- Do not expand a focused implementation task into broader redesign.

Follow the target repository's engineering principles and verification policy rather than duplicating their content in this skill.