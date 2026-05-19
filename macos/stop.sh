#!/bin/bash
# Auto Controller - macOS 停止脚本

echo "停止服务..."

# 读取 PID 并停止
if [ -f .app.pid ]; then
    kill $(cat .app.pid) 2>/dev/null
    rm -f .app.pid
fi

if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm -f .backend.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm -f .frontend.pid
fi

# 通过端口强制释放
for port in 5001 5173; do
    pid=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pid" ]; then
        kill -9 $pid 2>/dev/null
        echo "已释放端口 $port"
    fi
done

# 确保进程已停止
pkill -f "python.*module/main.py" 2>/dev/null
pkill -f "Electron" 2>/dev/null

echo "服务已停止"
