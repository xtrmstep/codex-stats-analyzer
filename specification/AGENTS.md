# Specification

This directory is the single source of truth for the intended system behavior, architecture, and interfaces. It is the authoritative reference for implementation and future changes.

## Purpose

Specifications define what the system must do and how components must interact. The specification describes the intended target system, not necessarily the current implementation. Existing code must not silently override the specification.

## Structure

```
specification/
├── AGENTS.md                          — this file; single entry point
├── codex-usage-analyzer.md            — comprehensive product specification
│
├── 01-screens/
│   ├── AGENTS.md                      — conventions for screen specifications
│   ├── 000-main-layout.md             — application shell and regions
│   ├── 010-navigation.md
│   ├── 020-header.md
│   └── 030-content.md
│
├── 02-architecture/
│   ├── 01-guidelines/                 — engineering and documentation conventions
│   │   ├── 010-engineering-principles.md
│   │   ├── 020-naming-conventions.md
│   │   ├── 030-code-style.md
│   │   ├── 040-verification.md
│   │   └── 050-diagram-guidelines.md
│   └── 02-design/                     — reserved for future architecture design documents
│
└── 03-contracts/
    └── AGENTS.md                      — conventions for contract specifications
```

## Navigation

- **Product requirements:** start with [codex-usage-analyzer.md](./codex-usage-analyzer.md).
- **UI behavior:** read [01-screens/AGENTS.md](./01-screens/AGENTS.md), then the relevant screen documents in [01-screens/](./01-screens/).
- **Engineering conventions:** read the applicable guideline in [02-architecture/01-guidelines/](./02-architecture/01-guidelines/).
- **Interface contracts:** read [03-contracts/AGENTS.md](./03-contracts/AGENTS.md).

## Document conventions

- Three-digit numeric prefixes determine document order; use increments of ten.
- Use relative Markdown links for cross-references.
- Each requirement lives in one authoritative location; link instead of duplicating.
- Preserve existing document numbers and filenames when possible.
- Allow intermediate numbers (e.g., `015`) when inserting documents between existing ones.

## Agent workflow

- Read relevant specifications before implementation.
- Follow applicable engineering conventions from `02-architecture/01-guidelines/`.
- Implement the smallest change satisfying the specification.
- Report contradictions, missing requirements, and differences between specification and implementation.
- Keep specification-only changes separate from implementation changes.
- Verify relative links and numbering consistency when updating documents.
- Do not modify unrelated implementation code while updating specifications.
