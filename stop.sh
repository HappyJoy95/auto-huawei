#!/bin/bash
# Auto Controller - macOS 停止脚本

echo "停止服务..."

# 读取 PID 并停止
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi

# 确保进程已停止
pkill -f "python.*module/main.py" 2>/dev/null
pkill -f "Electron" 2>/dev/null

echo "服务已停止"
