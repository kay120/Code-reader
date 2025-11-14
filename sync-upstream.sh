#!/bin/bash

# 同步上游仓库脚本
# 用途: 从 The-Agent-Builder/Code-reader 同步最新代码到本地和您的 fork

set -e  # 遇到错误立即退出

echo "🔄 开始同步上游代码..."
echo ""

# 1. 确保在 main 分支
echo "📍 切换到 main 分支..."
git checkout main

# 2. 从上游获取最新代码
echo "⬇️  从上游仓库获取最新代码..."
git fetch upstream

# 3. 合并上游 master 分支到本地 main 分支
echo "🔀 合并上游 master 分支..."
git merge upstream/master

# 4. 推送到您的 fork
echo "⬆️  推送到您的 fork..."
git push origin main

echo ""
echo "✅ 同步完成!"
echo "📊 当前状态:"
git status

