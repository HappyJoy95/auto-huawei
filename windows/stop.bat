@echo off
echo ========================================
echo   Stopping all services...
echo ========================================
echo.

:: Kill ONLY project-related processes by port, NOT global process names

echo Stopping Vite server on port 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Stopping Electron processes...
taskkill /F /IM electron.exe >nul 2>&1

echo Stopping Python processes on port 5001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ========================================
echo   All services stopped
echo ========================================
pause
