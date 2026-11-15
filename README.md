# Codex Usage Analyzer

A local Windows dashboard for exploring Codex token usage and agent activity.

## Data sources

The app imports local JSONL logs from `%USERPROFILE%\.codex\sessions` and `%USERPROFILE%\.codex\archived_sessions` into SQLite. Edit `config.toml` to change the source folders.

## Dashboard

Streamlit shows usage totals and trends in tables and interactive charts. Filter by date, project, model, agent role, chat, or agent.

## Run locally

Install Python 3.12 on Windows and add it to PATH. Run these commands from the project folder.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run.bat
```

Open [http://localhost:8501](http://localhost:8501).
