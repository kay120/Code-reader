#!/bin/bash

# Celery Worker 启动脚本
# 解决模块导入问题

# 切换到backend目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境
source .venv/bin/activate

# 设置PYTHONPATH - 确保backend目录在Python路径中
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

echo "=== Celery Worker 启动配置 ==="
echo "工作目录: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"
echo "Python版本: $(python --version)"
echo "Celery版本: $(celery --version)"
echo "================================"

# 启动Celery Worker
exec celery -A celery_app worker \
    --loglevel=info \
    --concurrency=10 \
    --queues=analysis

