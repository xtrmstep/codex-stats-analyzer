# Contract Guidelines

This document defines how interfaces between system components should be specified.

## Purpose

Contracts define agreed interfaces and data structures between components, applications, or external systems. Examples include frontend/backend communication, service APIs, events, and shared configuration schemas.

## Organization

- `api/` — HTTP APIs and other service interface definitions.
- `schemas/` — shared data structures and configuration schemas.
- `events/` — event and message contracts.

Create these subdirectories only when they contain actual contracts. Avoid empty placeholder directories.

Additional categories may be introduced when justified by a concrete need.

## Format conventions

- Prefer OpenAPI for HTTP API definitions.
- Prefer JSON Schema for JSON-based data structures.
- Use appropriate machine-readable formats for event contracts when applicable.
- Use Markdown for explanations that cannot be expressed clearly in the contract definition itself.

## Required contract qualities

Contracts should explicitly define applicable:

- Field names and data types.
- Required and optional fields.
- Validation constraints.
- Request and response structures.
- Error representations.
- Compatibility requirements.
- Event or message semantics.

## General rules

- Keep contracts independent from internal implementation classes.
- Reuse shared schemas when they represent the same concept.
- Avoid unnecessary duplication.
- Keep producer and consumer expectations consistent.
- Do not silently introduce breaking interface changes.
- Reference contracts from screens and architecture documents when applicable.
- Preserve existing contract identifiers and filenames when changing them would break references or consumers.

Do not create speculative API definitions or schema examples.
