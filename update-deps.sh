#!/bin/bash

# 更新依赖脚本
# 用途: 更新 Python 和 Node.js 依赖

set -e  # 遇到错误立即退出

echo "📦 开始更新依赖..."
echo ""

# 更新 Python 依赖
echo "🐍 更新 Python 依赖 (uv)..."
uv sync --upgrade

echo ""

# 更新前端依赖
echo "📱 更新前端依赖 (pnpm)..."
cd frontend
pnpm update
cd ..

echo ""
echo "✅ 依赖更新完成!"
echo ""
echo "ℹ️  注意: uv.lock 和 pnpm-lock.yaml 已被 .gitignore 忽略"
echo "   这些文件不会被提交到仓库"

