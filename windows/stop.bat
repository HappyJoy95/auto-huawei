@echo off
cd /d %~dp0
echo ========================================
echo   Stopping all services...
echo ========================================
echo.

:: Kill ONLY project-related processes by port, NOT global process names

echo Stopping Vite server on port 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Stopping Python backend on port 5001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Stop Electron only if it was launched by this project (via PID file)
if exist .app.pid (
    set /p APP_PID=<.app.pid
    taskkill /F /T /PID %APP_PID% >nul 2>&1
    del .app.pid >nul 2>&1
    echo Stopped Electron (PID %APP_PID%)
) else (
    echo No .app.pid found, skipping Electron stop
)

echo.
echo ========================================
echo   All services stopped
echo ========================================
pause
