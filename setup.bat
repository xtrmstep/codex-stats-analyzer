@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
    echo Python launcher not found. Install Python 3.12 for Windows, then retry.
    exit /b 1
)
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 not found. Install Python 3.12 for Windows, then retry.
    exit /b 1
)
py -3.12 -m venv .venv
if errorlevel 1 (
    echo Could not create .venv. Check permissions and the Python installation.
    exit /b 1
)
if "%~1"=="" (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
    ".venv\Scripts\python.exe" -m pip install --no-index --find-links "%~1" -r requirements.txt
)
if errorlevel 1 (
    echo Dependency installation failed. Check connectivity or the supplied wheel directory.
    exit /b 1
)
echo Setup complete. Run run.bat to start the application.

