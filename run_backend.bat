@echo off
echo ========================================================
echo Starting SATYA-APAAR Backend Server (FastAPI)
echo ========================================================
cd /d "%~dp0backend"
if exist venv\Scripts\python.exe (
    set PYTHON_EXEC=venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

echo Starting uvicorn on http://127.0.0.1:8000 ...
%PYTHON_EXEC% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
