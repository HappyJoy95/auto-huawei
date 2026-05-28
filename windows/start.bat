@echo off
cd /d %~dp0

echo ========================================
echo   Auto Controller Starting (Windows)
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

:: Check Vite server (only for development mode)
echo [1/3] Starting Vite dev server...
curl -s http://localhost:5173 >nul 2>&1
if %errorlevel%==0 (
    echo [Vite] Server already running
) else (
    start "Vite Dev Server" /min cmd /c "set PLATFORM_ROOT=%CD%&& cd ..\shared\packages\renderer&& ..\..\..\windows\node_modules\.bin\vite --host"
    timeout /t 3 /nobreak >nul
)

:: Start Electron using npx (Python backend managed by Electron internally)
echo [3/3] Starting Electron App...
echo.
echo ========================================
echo   Application starting in desktop window...
echo   (Python backend will be managed by Electron)
echo   (Do not close this window)
echo ========================================
echo.
set NODE_ENV=development
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process -FilePath '.\node_modules\electron\dist\electron.exe' -ArgumentList '.' -PassThru; Set-Content -Path '.app.pid' -Value $p.Id; Wait-Process -Id $p.Id"
if exist .app.pid del .app.pid >nul 2>&1

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
