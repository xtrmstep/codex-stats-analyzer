# Verification

This document defines how implementation and specification changes should be verified.

## Policy: unit tests are not required

Do not introduce new unit tests or test infrastructure unless explicitly requested. Existing tests must not be removed or deliberately broken.

## Required verification approach

Use appropriate checks based on the nature of the change:

- Syntax and compilation checks.
- Static analysis and linting where tools exist.
- Type checking where configured.
- LLM-assisted analysis of correctness, consistency, and specification compliance.
- Review of affected interfaces, dependencies, and contracts.
- Targeted execution or integration checks when necessary and feasible.

## Documentation-only changes

For documentation-only changes, verify:

- Markdown structure and readability.
- Relative links and references.
- Numbering conventions.
- Consistency with related specifications.
- That no existing requirements have been unintentionally removed.

## Reporting

Agents must report which checks were performed and identify checks that could not be performed.

Static analysis and LLM review do not guarantee runtime correctness; acknowledge this explicitly when only these checks are available.

Do not require installing new verification frameworks or introducing unnecessary tools.
