@echo off

REM Check the app configuration before starting Streamlit.
".venv\Scripts\python.exe" app.py --check-config || exit /b 1
".venv\Scripts\python.exe" -m streamlit run app.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false
