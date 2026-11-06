# 01 — Application foundation and Windows launchers

Status: Implementation complete; independent review pending | Phase: 1 | Dependencies: None

Specification: §§1, 8, 9, 11.

## Scope

- Establish `app.py`, `parser.py`, `analytics.py`, `annotations.py`, `requirements.txt`, `config.toml`, `setup.bat`, `run.bat`, and `data/` as described in the specification.
- Select and document a supported Python version and compatible dependencies. Configure the two default Codex source directories and additional directories.
- Create a project-local virtual environment during setup; launch from the project directory regardless of the caller's working directory. Handle Windows paths containing spaces and missing prerequisites with clear messages.
- Bind Streamlit to localhost on port 8501 and disable telemetry. Avoid remote assets and runtime service dependencies.
- Exclude private source data, generated local metadata, and the virtual environment from version control.

## Acceptance and validation

- On Windows, setup prepares dependencies and run opens the local application using that environment.
- Configuration resolves `%USERPROFILE%` correctly and supports additional source paths.
- Verify localhost binding and telemetry settings; runtime requires neither network nor Codex credentials.
- Provide a minimal startup smoke check and actionable errors for invalid configuration.

## Validation evidence

- Windows `setup.bat` created the Python 3.12 environment and installed the declared dependencies.
- Python 3.12 compiled the four modules; `app.py --check-config` expanded both default paths, and an empty directory list produced an actionable error.
- `run.bat` started Streamlit on localhost:8501; the local health endpoint returned `ok`. Effective configuration reported localhost, port 8501, telemetry disabled, and the first-run email prompt disabled.
- Offline wheelhouse installation, launch from a path containing spaces, and an offline browser session have not been exercised.
- Independent review remains pending.

