# Diagram Guidelines

This document defines conventions for architecture diagrams. It does not create system-specific diagrams.

## General conventions

- Use Mermaid embedded in Markdown as the default diagram format.
- Keep diagrams readable and focused on a specific architectural concern.
- Show important relationships without reproducing all implementation details.
- Use consistent names and terminology aligned with the specification.
- Keep diagrams aligned with the accompanying textual specification.
- Prefer multiple focused diagrams over one overloaded diagram.
- Do not duplicate information unnecessarily between diagrams.

## System overview diagrams

- Show major subsystems, boundaries, and external dependencies.
- Focus on the overall organization of the system.
- Exclude low-level classes and implementation details.

## Component diagrams

- Show major components, responsibilities, dependencies, and interfaces.
- Make communication direction explicit when relevant.
- Group components according to meaningful system boundaries.

## Class diagrams

- Include important classes and interfaces.
- Show significant inheritance, composition, and dependencies.
- Focus on responsibilities and public relationships.
- Avoid documenting every method, field, or helper class.
- Do not automatically generate large class diagrams from the entire codebase.

## Flowcharts

- Describe significant processing steps and decisions.
- Make branching conditions understandable.
- Include relevant error handling or failure paths.
- Avoid unnecessary low-level implementation steps.

## Sequence diagrams

- Describe important interactions between components over time.
- Identify participants clearly.
- Show significant requests, responses, and asynchronous interactions.
- Avoid excessive detail.

## Organization

- Store actual system design documents under `02-architecture/02-design/`.
- Use numbered documents and relative references.
- Introduce `000-system-overview.md` when the system-level architecture is first defined.
- Add dedicated design documents only when necessary.

Do not create empty diagram templates or speculative architecture documents.
