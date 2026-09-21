@echo off
cd /d "%~dp0"

if not exist venv\Scripts\activate.bat (
    echo Virtual environment not found.
    echo Run the first-time setup steps in README.md before using this shortcut.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
uvicorn app.main:app --port 8000

echo.
echo Backend stopped.
pause
