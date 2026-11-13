---
name: manage-specification
description: Create, update, reorganize, or review the system specification, including screens, architecture, contracts, diagrams, and their cross-references. Use for specification-only tasks; not for implementing application code.
---

# Manage Specification

Use the repository's specification as the authoritative definition of intended behavior and design. This skill describes **how to make changes**; it does not replace the specification's rules.

## Workflow

1. Read the repository's root `AGENTS.md` and `specification/AGENTS.md`, if present.
2. If `specification/` is missing, request or follow the repository's bootstrap task; do not invent a new specification framework.
3. Find the relevant screen, architecture, or contract documents. Read their local guidelines and linked specifications. Inspect only the necessary repository context.
4. Identify the authoritative document for the requested change. Extend an existing document where possible; add a numbered document only when its scope justifies separation.
5. Change the smallest set of documents needed. Preserve established requirements, numbering, names, and conventions unless the task specifically changes them.
6. Check references and impacts across screens, architecture, contracts, and existing implementation. Update affected specification documents and relative links without copying authoritative content.
7. Verify Markdown structure, numbering, links, consistency, and preservation of unrelated requirements. Use available checks; do not introduce new tooling solely for this.
8. Report changed documents, verification performed, unresolved decisions, and any known gap between code and specification.

## Boundaries

- Do not change application code or tests unless explicitly requested.
- Do not create speculative screens, classes, diagrams, or contracts.
- Do not silently reconcile contradictions or make up requirements; explain unresolved conflicts.
- Do not treat existing code as authority over intended behavior.
- Keep the specification readable to humans; do not add redundant entry points or metadata registries.

Follow the target repository's guidelines for document layout, numbering, and scope rather than restating those rules here.