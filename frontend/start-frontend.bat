@echo off
cd /d "%~dp0"

if not exist node_modules (
    echo Dependencies not installed.
    echo Run "npm install" in this folder first (see README.md).
    pause
    exit /b 1
)

npm run dev

echo.
echo Frontend stopped.
pause
