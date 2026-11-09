# Engineering Principles

This document defines the general engineering philosophy for the project. These principles guide implementation and design decisions.

## Priority order

When principles conflict, apply the following priority:

1. Correctness and specification compliance.
2. Simplicity and readability.
3. Maintainability.
4. Minimal scope of changes.
5. Reuse and abstraction when justified.

## First-principles thinking

- Understand the actual requirements before designing a solution.
- Challenge unnecessary assumptions.
- Solve the underlying problem rather than automatically preserving historical complexity.

## Simplicity

- Prefer the simplest solution that fully satisfies the requirements.
- Follow KISS and YAGNI.
- Avoid premature abstractions, unnecessary extensibility, and speculative functionality.
- Do not introduce additional layers, classes, or interfaces without clear justification.

## SOLID

- Apply SOLID principles where they improve maintainability.
- Prefer clear responsibilities and explicit dependencies.
- Do not apply SOLID mechanically when doing so increases complexity without practical benefit.

## DRY

- Avoid unnecessary duplication of logic.
- Do not introduce abstractions solely to eliminate small, incidental repetition.
- Favor readable, locally understandable code over excessive reuse.

## Minimal changes

- Make the smallest meaningful change needed to meet the requirements.
- Preserve existing behavior outside the requested scope.
- Avoid unrelated cleanup, restructuring, and refactoring.
- Follow existing conventions unless a change explicitly requires otherwise.

## Maintainability

- Prioritize correctness, readability, and ease of modification.
- Prefer understandable solutions over technically elaborate ones.
- Keep dependencies and interactions explicit.
- Use established project technologies before introducing new dependencies.

These principles are pragmatic guides, not rigid architectural dogma. Engineering judgment is always required.
