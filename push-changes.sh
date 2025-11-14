#!/bin/bash

# 推送修改脚本
# 用途: 提交并推送您的修改到 fork

set -e  # 遇到错误立即退出

echo "📝 准备提交并推送修改..."
echo ""

# 检查是否有修改
if [[ -z $(git status -s) ]]; then
    echo "ℹ️  没有需要提交的修改"
    exit 0
fi

# 显示当前修改
echo "📋 当前修改:"
git status -s
echo ""

# 询问提交信息
read -p "💬 请输入提交信息: " commit_message

if [[ -z "$commit_message" ]]; then
    echo "❌ 提交信息不能为空"
    exit 1
fi

# 添加所有修改
echo "➕ 添加修改..."
git add .

# 提交
echo "💾 提交修改..."
git commit -m "$commit_message"

# 推送到 fork
echo "⬆️  推送到您的 fork..."
git push origin main

echo ""
echo "✅ 推送完成!"
echo "🔗 您的仓库: https://github.com/kay120/Code-reader"

