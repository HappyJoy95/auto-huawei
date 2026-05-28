@echo off
cd /d %~dp0

echo ========================================
echo Auto Controller - 开发模式
echo ========================================

:: 启动 Python 后端
echo [1/3] 启动 Python 后端...
start "Python Backend" cmd /c "venv\Scripts\python.exe module\main.py"
timeout /t 3 /nobreak >nul

:: 启动 Vite 开发服务器
echo [2/3] 启动前端开发服务器...
start "Vite Dev Server" cmd /c "set PLATFORM_ROOT=%CD%&& cd ..\shared\packages\renderer&& ..\..\..\windows\node_modules\.bin\vite"
timeout /t 5 /nobreak >nul

:: 启动 Electron
echo [3/3] 启动 Electron...
set NODE_ENV=development
npx electron .

echo ========================================
echo 已关闭
pause
