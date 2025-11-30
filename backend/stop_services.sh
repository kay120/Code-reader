#!/bin/bash

# Code Reader 服务停止脚本
# 用于停止所有服务: FastAPI Backend, Celery Worker

echo "========================================="
echo "  Code Reader 服务停止脚本"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 停止后端服务
echo "1️⃣  停止后端服务..."
if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✅ 后端服务已停止${NC}"
else
    echo "   后端服务未运行"
fi
echo ""

# 停止 Celery worker
echo "2️⃣  停止 Celery worker..."
if pgrep -f "celery.*worker" > /dev/null; then
    pkill -f "celery.*worker"
    sleep 2
    echo -e "${GREEN}✅ Celery worker 已停止${NC}"
else
    echo "   Celery worker 未运行"
fi
echo ""

# 询问是否停止 Redis
echo "3️⃣  Redis 容器管理"
echo -e "${YELLOW}   Redis 可能被其他项目使用,是否停止? (y/N)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    if docker ps | grep -q "redis.*6379"; then
        REDIS_CONTAINER=$(docker ps | grep "redis.*6379" | awk '{print $1}')
        docker stop $REDIS_CONTAINER
        echo -e "${GREEN}✅ Redis 容器已停止${NC}"
    else
        echo "   Redis 容器未运行"
    fi
else
    echo "   保持 Redis 运行"
fi
echo ""

echo "========================================="
echo -e "${GREEN}✅ 服务停止完成${NC}"
echo "========================================="
echo ""
echo "💡 提示:"
echo "   - 重新启动: ./start_services.sh"
echo "   - 查看进程: ps aux | grep -E 'celery|uvicorn|python.*run.py'"
echo ""

