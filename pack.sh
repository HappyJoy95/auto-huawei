#!/bin/bash
# 打包项目用于迁移

VERSION="0.1.1-mac"
OUTPUT="auto-controller-${VERSION}.tar.gz"

echo "打包 Auto Controller ${VERSION}..."

# 排除不需要的目录
tar --exclude='node_modules' \
    --exclude='venv' \
    --exclude='data' \
    --exclude='.DS_Store' \
    --exclude='*.pid' \
    --exclude='*.log' \
    --exclude='release' \
    -czvf "$OUTPUT" .

echo ""
echo "打包完成: $OUTPUT"
echo "文件大小: $(du -h "$OUTPUT" | cut -f1)"
echo ""
echo "将此文件复制到目标机器后："
echo "  tar -xzvf $OUTPUT"
echo "  ./install.sh"
