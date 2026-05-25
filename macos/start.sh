#!/bin/bash
# Auto Controller - macOS 启动脚本

cd "$(dirname "$0")"

# 删除可能存在的 ELECTRON_RUN_AS_NODE 环境变量
# 这个变量会导致 Electron 以 Node.js 模式运行，而不是 Electron 模式
unset ELECTRON_RUN_AS_NODE

echo "========================================"
echo "  Auto Controller v0.1.0 (macOS)"
echo "========================================"

# 检查 Python 虚拟环境
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装 Python 依赖
echo "检查 Python 依赖..."
pip install -r requirements.txt -q

# 检查 Node 依赖
if [ ! -d "node_modules" ]; then
    echo "安装 Node.js 依赖..."
    npm install
fi

# 启动应用（Electron 会自动管理 Python 后端）
echo "启动应用..."
export NODE_ENV=production
./node_modules/electron/dist/Electron.app/Contents/MacOS/Electron . &
APP_PID=$!
echo "应用 PID: $APP_PID"

echo ""
echo "========================================"
echo "服务已启动！"
echo "使用 ./stop.sh 停止服务"
echo "========================================"

# 保存 PID 到文件
echo $APP_PID > .app.pid

# 等待
wait
