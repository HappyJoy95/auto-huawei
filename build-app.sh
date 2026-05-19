#!/bin/bash
# Auto Controller - macOS 打包脚本

cd "$(dirname "$0")"

echo "========================================"
echo "  Auto Controller - 打包 macOS 应用"
echo "========================================"

# 检查是否安装了依赖
if [ ! -d "node_modules" ]; then
    echo "请先运行 ./install.sh 安装依赖"
    exit 1
fi

# 检查是否构建了前端
if [ ! -f "packages/main/dist/main.cjs" ]; then
    echo "构建前端..."
    npm run build
fi

echo ""
echo "开始打包..."
npx electron-builder --mac

echo ""
echo "========================================"
echo "打包完成！"
echo "应用位于 release/ 目录"
echo "========================================"
