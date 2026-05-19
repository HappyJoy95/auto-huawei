@echo off
cd /d %~dp0

echo ========================================
echo   Auto Controller Starting...
echo ========================================
echo.

:: Kill old processes (ONLY project-related ones)
echo [Cleanup] Closing old project processes...

:: Kill Python on port 5001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Kill Vite on port 5173
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Check Python backend
echo [1/4] Starting Python backend...
curl -s http://127.0.0.1:5001/api/health >nul 2>&1
if %errorlevel%==0 (
    echo [Python] Backend already running
) else (
    start "Python Backend" /min cmd /c "venv\Scripts\python.exe module\main.py"
    timeout /t 3 /nobreak >nul
)

:: Check Vite server (only for development mode)
echo [2/4] Starting Vite dev server...
curl -s http://localhost:5173 >nul 2>&1
if %errorlevel%==0 (
    echo [Vite] Server already running
) else (
    start "Vite Dev Server" /min cmd /c "cd packages\renderer && npx vite --host"
    timeout /t 5 /nobreak >nul
)

:: Start Electron using npx (no hardcoded path!)
echo [4/4] Starting Electron App...
echo.
echo ========================================
echo   Application starting in desktop window...
echo   (Do not close this window)
echo ========================================
echo.
set NODE_ENV=development
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
npx electron .

echo.
echo ========================================
echo   Application closed
echo ========================================
echo.
echo Cleaning up...
:: Cleanup ONLY project ports, not all node processes
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

pause
