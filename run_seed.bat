@echo off
echo ========================================================
echo SATYA-APAAR Database Seeding (Synthetic SIH Data)
echo ========================================================
cd /d "%~dp0backend"
if exist venv\Scripts\python.exe (
    set PYTHON_EXEC=venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

echo Using Python: %PYTHON_EXEC%
%PYTHON_EXEC% seed/synthetic_seed.py
echo.
echo Seeding finished.
pause
