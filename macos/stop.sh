#!/bin/bash
# Auto Controller - macOS 停止脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "停止服务..."

stop_pid() {
    local pid="$1"
    local name="$2"

    if [ -z "$pid" ]; then
        return
    fi

    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null
        echo "已发送停止信号到 $name PID $pid"
    fi
}

for pidfile in .app.pid .backend.pid .frontend.pid; do
    path="$SCRIPT_DIR/$pidfile"
    if [ -f "$path" ]; then
        pid=$(cat "$path")
        stop_pid "$pid" "$pidfile"
        rm -f "$path"
    fi
done

sleep 2

for port in 5001 5173; do
    pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            cmd=$(ps -o command= -p "$pid" 2>/dev/null)
            if echo "$cmd" | grep -Fq "$SCRIPT_DIR"; then
                kill -9 "$pid" 2>/dev/null
                echo "已强制释放端口 $port (PID $pid)"
            else
                echo "跳过端口 $port 上的非本项目进程 (PID $pid)"
            fi
        done
    fi
done

pkill -TERM -P $$ 2>/dev/null || true

echo "服务已停止"
