@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Project environment not found. Run setup.bat first.
    exit /b 1
)
".venv\Scripts\python.exe" app.py --check-config
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m streamlit run app.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false
if errorlevel 1 (
    echo Application failed to start. Run setup.bat to check dependencies.
    exit /b 1
)
