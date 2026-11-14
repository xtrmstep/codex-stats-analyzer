@echo off

pushd "%~dp0" || exit /b 1

REM Check the app configuration before starting Streamlit.
".venv\Scripts\python.exe" "src\app.py" --check-config
if errorlevel 1 (
    popd
    exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run "src\app.py" --server.address localhost --server.port 8501 --browser.gatherUsageStats false
set "app_exit_code=%ERRORLEVEL%"
popd
exit /b %app_exit_code%
