#!/bin/bash
# Auto Controller - macOS 一键安装脚本

cd "$(dirname "$0")"

echo "========================================"
echo "  Auto Controller v0.1.0 - macOS 安装"
echo "========================================"

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "请先安装 Homebrew: https://brew.sh"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "安装 Node.js..."
    brew install node
fi

# 检查 Python 3
if ! command -v python3 &> /dev/null; then
    echo "安装 Python 3..."
    brew install python3
fi

echo ""
echo "========================================"
echo "1. 安装 Node.js 依赖..."
echo "========================================"
npm install

echo ""
echo "========================================"
echo "2. 创建 Python 虚拟环境..."
echo "========================================"
python3 -m venv venv
source venv/bin/activate

echo ""
echo "========================================"
echo "3. 安装 Python 依赖..."
echo "========================================"
pip install -r requirements.txt

echo ""
echo "========================================"
echo "4. 构建前端..."
echo "========================================"
npm run build

echo ""
echo "========================================"
echo "安装完成！"
echo ""
echo "使用方法："
echo "  ./start.sh    启动应用"
echo "  ./stop.sh     停止应用"
echo "========================================"
