# Code Style

This document defines general coding and documentation rules for the project.

## Code organization

- Prefer small, focused classes and functions with single clear responsibilities.
- Maintain clear separation of responsibilities between modules.
- Avoid excessive nesting and unnecessary indirection.
- Prefer composition and explicit dependencies over deep inheritance.
- Follow established repository formatting and coding conventions.

## Comments and documentation

- Use Google-style docstrings for Python classes and public methods.
- Document purpose, parameters, return values, and exceptions where applicable.
- Keep docstrings concise and avoid repeating information already clear from names or type hints.
- Explain intent, reasoning, and important constraints in inline comments.
- Avoid comments that merely repeat what the code already expresses.
- Avoid verbose documentation for trivial or self-explanatory implementation details.
- Keep documentation synchronized with behavior.

**Google-style docstring example:**

```python
def load_sessions(directory: str) -> list[Session]:
    """Load all sessions from the given directory.

    Args:
        directory: Path to the directory containing JSONL session files.

    Returns:
        A list of parsed Session objects.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
```

## Implementation discipline

- Avoid unnecessary dependencies and abstractions.
- Do not introduce unrelated refactoring within a change.
- Maintain compatibility with existing interfaces unless explicitly changed.
- Prefer clear code over clever or highly compressed expressions.
- Remove code made obsolete by the current change; do not leave dead code.
