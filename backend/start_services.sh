#!/bin/bash

# Code Reader 服务启动脚本
# 用于启动所有必需的服务: Redis, Celery Worker, FastAPI Backend

set -e  # 遇到错误立即退出

echo "========================================="
echo "  Code Reader 服务启动脚本"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker 是否运行
echo "1️⃣  检查 Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行,请先启动 Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 运行正常${NC}"
echo ""

# 检查 Redis 容器
echo "2️⃣  检查 Redis..."
if docker ps | grep -q "redis.*6379"; then
    REDIS_CONTAINER=$(docker ps | grep "redis.*6379" | awk '{print $1}')
    echo -e "${GREEN}✅ Redis 已运行 (容器: $REDIS_CONTAINER)${NC}"
else
    echo -e "${YELLOW}⚠️  Redis 未运行,正在启动...${NC}"
    
    # 检查是否有停止的 Redis 容器
    if docker ps -a | grep -q "code-reader-redis"; then
        echo "   启动现有容器..."
        docker start code-reader-redis
    else
        echo "   创建新容器..."
        docker run -d \
            --name code-reader-redis \
            -p 6379:6379 \
            --health-cmd "redis-cli ping" \
            --health-interval 5s \
            redis:7-alpine
    fi
    
    # 等待 Redis 就绪
    echo "   等待 Redis 就绪..."
    sleep 3
    
    if docker exec $(docker ps | grep redis | awk '{print $1}') redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis 启动成功${NC}"
    else
        echo -e "${RED}❌ Redis 启动失败${NC}"
        exit 1
    fi
fi
echo ""

# 检查虚拟环境
echo "3️⃣  检查 Python 虚拟环境..."
if [ -d ".venv" ]; then
    echo -e "${GREEN}✅ 虚拟环境存在${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠️  虚拟环境不存在,请先创建: python -m venv .venv${NC}"
    exit 1
fi
echo ""

# 停止旧的 Celery worker
echo "4️⃣  停止旧的 Celery worker..."
pkill -f "celery.*worker" 2>/dev/null && echo -e "${GREEN}✅ 已停止旧的 worker${NC}" || echo "   没有运行中的 worker"
echo ""

# 启动 Celery worker
echo "5️⃣  启动 Celery worker..."
# 使用12个并发worker以充分利用API限制(并发100, RPM 500)
nohup celery -A celery_app worker \
    --loglevel=info \
    --concurrency=12 \
    --queues=analysis > celery_worker.log 2>&1 &

sleep 3

if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "${GREEN}✅ Celery worker 启动成功${NC}"
    echo "   日志文件: celery_worker.log"
else
    echo -e "${RED}❌ Celery worker 启动失败${NC}"
    exit 1
fi
echo ""

# 停止旧的后端服务
echo "6️⃣  停止旧的后端服务..."
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✅ 已停止旧的后端服务${NC}" || echo "   没有运行中的后端服务"
sleep 2
echo ""

# 启动后端服务
echo "7️⃣  启动后端服务..."
nohup python run.py > backend.log 2>&1 &

sleep 5

# 检查后端服务
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务启动成功${NC}"
    echo "   API 地址: http://localhost:8000"
    echo "   API 文档: http://localhost:8000/docs"
    echo "   日志文件: backend.log"
else
    echo -e "${RED}❌ 后端服务启动失败,查看日志: tail -f backend.log${NC}"
    exit 1
fi
echo ""

echo "========================================="
echo -e "${GREEN}🎉 所有服务启动成功!${NC}"
echo "========================================="
echo ""
echo "📊 服务状态:"
echo "   - Redis:        运行中 (端口 6379)"
echo "   - Celery:       运行中 (4 workers)"
echo "   - Backend API:  运行中 (端口 8000)"
echo ""
echo "📝 查看日志:"
echo "   - Celery:  tail -f celery_worker.log"
echo "   - Backend: tail -f backend.log"
echo ""
echo "🛑 停止服务:"
echo "   - 停止所有: ./stop_services.sh"
echo "   - 停止 Celery: pkill -f 'celery.*worker'"
echo "   - 停止 Backend: lsof -ti:8000 | xargs kill -9"
echo ""

