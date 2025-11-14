#!/bin/bash

# 同步上游仓库脚本
# 用途: 从 The-Agent-Builder/Code-reader 同步最新代码到本地 main 分支和您的 fork
# 注意: main 分支用于镜像上游,不要在 main 分支直接开发

set -e  # 遇到错误立即退出

echo "🔄 开始同步上游代码到 main 分支..."
echo ""

# 1. 确保在 main 分支
echo "📍 切换到 main 分支..."
git checkout main

# 2. 从上游获取最新代码
echo "⬇️  从上游仓库获取最新代码..."
git fetch upstream

# 3. 合并上游 master 分支到本地 main 分支
echo "🔀 合并上游 master 分支到 main..."
git merge upstream/master

# 4. 推送到您的 fork 的 main 分支
echo "⬆️  推送到您的 fork 的 main 分支..."
git push origin main

# 5. 切换回 dev 分支
echo "🔄 切换回 dev 分支..."
git checkout dev

echo ""
echo "✅ 同步完成!"
echo "💡 提示: main 分支已更新,您现在在 dev 分支"
echo "   如需将 main 的更新合并到 dev,请运行: ./merge-main-to-dev.sh"
echo ""
echo "📊 当前状态:"
git status

