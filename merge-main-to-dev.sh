#!/bin/bash

# 合并 main 到 dev 脚本
# 用途: 将 main 分支的更新合并到 dev 分支

set -e  # 遇到错误立即退出

echo "🔀 开始将 main 分支合并到 dev 分支..."
echo ""

# 1. 确保在 dev 分支
echo "📍 切换到 dev 分支..."
git checkout dev

# 2. 合并 main 分支
echo "🔀 合并 main 分支到 dev..."
git merge main

# 3. 推送到您的 fork
echo "⬆️  推送到您的 fork 的 dev 分支..."
git push origin dev

echo ""
echo "✅ 合并完成!"
echo "📊 当前状态:"
git status

