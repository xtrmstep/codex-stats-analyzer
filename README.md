# Codex Usage Analyzer

A local Windows application for analyzing Codex usage. This initial foundation displays configured session directories; analytics are not yet implemented. It needs no Codex authentication or network connection at runtime.

## Setup and start

Install Python 3.12 for Windows with the Python launcher, then run `setup.bat`. It creates `.venv` in this directory and installs Streamlit, pandas, and Plotly. Run `run.bat` to open the application at http://localhost:8501. Both launchers work from any working directory, including paths containing spaces.

For offline installation, supply a directory containing compatible Python 3.12 Windows wheels for all requirements and their transitive dependencies: `setup.bat "C:\path to\wheelhouse"`. Prepare that wheelhouse on a connected machine with `py -3.12 -m pip download -r requirements.txt -d wheelhouse` using the target Windows platform and architecture. The offline setup uses only that directory.

Edit `config.toml` to add source directories to `sources.directories`. `%USERPROFILE%` and other Windows environment variables are expanded at startup. Relative paths are resolved from the project directory. Source directories need not exist yet. To check configuration without launching Streamlit, run `.venv\Scripts\python.exe app.py --check-config` from the project directory.

Streamlit listens on localhost port 8501 with usage telemetry disabled. Local metadata belongs in `data/` and is excluded from version control; the source JSONL files remain separate.

