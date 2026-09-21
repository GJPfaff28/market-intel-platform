@echo off
cd /d "%~dp0"

echo Starting Morning Scanner Dashboard...
echo.
echo   Backend and frontend will each open in their own window.
echo   Leave both windows open while you use the dashboard.
echo   Close this window's two children (or Ctrl+C in each) to stop.
echo.

start "Morning Scanner - Backend" cmd /k "cd /d "%~dp0backend" && start-backend.bat"
timeout /t 4 /nobreak >nul

start "Morning Scanner - Frontend" cmd /k "cd /d "%~dp0frontend" && start-frontend.bat"
timeout /t 5 /nobreak >nul

start http://localhost:5173

echo Done. Your browser should open shortly. This window can be closed.
pause
