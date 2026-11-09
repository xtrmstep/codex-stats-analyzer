# Naming Conventions

This document defines consistent naming expectations for the project. The project uses Python; conventions below apply to Python code.

## General rules

- Names must communicate purpose clearly.
- Prefer descriptive but concise names.
- Avoid misleading or excessively generic names (e.g., `data`, `temp`, `helper`).
- Use terminology consistently across related components.
- Follow standard Python (PEP 8) conventions unless the repository deviates explicitly.
- Avoid creating new naming schemes when repository conventions already exist.

## Python conventions

### Modules and packages

- Use `snake_case` for module and package names.
- Keep module names short but descriptive.
- Avoid redundant names that repeat the package path.

### Classes

- Use `PascalCase` for class names.
- Name classes after their primary responsibility.
- Avoid vague suffixes like `Manager`, `Handler`, or `Processor` unless they accurately describe the role.

### Functions and methods

- Use `snake_case` for function and method names.
- Use verb phrases that describe what the function does (e.g., `load_sessions`, `calculate_token_total`).
- Boolean functions should read as questions (e.g., `is_empty`, `has_label`).

### Variables and parameters

- Use `snake_case` for variable and parameter names.
- Use descriptive names that communicate the intent at the point of use.
- Avoid single-letter names except in short loops or mathematical contexts.

### Constants

- Use `UPPER_SNAKE_CASE` for constants.
- Define constants at module level.

### Private identifiers

- Prefix private module-level names and class members with a single underscore (`_`).
- Avoid name-mangling with double underscores unless required for inheritance protection.

## Abbreviations and acronyms

- Avoid unnecessary abbreviations.
- Use well-known abbreviations (e.g., `id`, `url`, `api`) consistently.
- Treat acronyms as words in `PascalCase` (e.g., `ApiClient`, not `APIClient`), unless the project already uses a different convention.
- Do not mix abbreviation styles within the same scope.
