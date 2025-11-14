#!/bin/bash

# 准备 Pull Request 脚本
# 用途: 将 dev 分支的修改合并到 main,准备提交 PR 到上游

set -e  # 遇到错误立即退出

echo "🎯 准备 Pull Request..."
echo ""

# 1. 确保 dev 分支是最新的
echo "📍 当前在 dev 分支,检查是否有未提交的修改..."
if [[ -n $(git status -s) ]]; then
    echo "⚠️  您有未提交的修改,请先提交"
    git status -s
    exit 1
fi

# 2. 切换到 main 分支
echo "📍 切换到 main 分支..."
git checkout main

# 3. 确保 main 是最新的
echo "🔄 确保 main 分支是最新的..."
git fetch upstream
git merge upstream/master
git push origin main

# 4. 合并 dev 到 main
echo "🔀 合并 dev 分支到 main..."
git merge dev

# 5. 推送到您的 fork
echo "⬆️  推送到您的 fork 的 main 分支..."
git push origin main

# 6. 切换回 dev 分支
echo "🔄 切换回 dev 分支..."
git checkout dev

echo ""
echo "✅ 准备完成!"
echo ""
echo "📝 下一步:"
echo "   1. 访问: https://github.com/kay120/Code-reader"
echo "   2. 点击 'Contribute' -> 'Open pull request'"
echo "   3. 创建 PR 到 The-Agent-Builder/Code-reader 的 master 分支"
echo ""
echo "💡 提示: 您现在在 dev 分支,可以继续开发"

