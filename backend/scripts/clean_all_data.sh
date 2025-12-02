#!/bin/bash

# ============================================
# 完整数据清理脚本
# 功能：清理所有数据但保留数据库结构
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
CODE_READER_ROOT="$(dirname "$BACKEND_DIR")"
PROJECT_ROOT="$(dirname "$CODE_READER_ROOT")"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   Code-reader 完整数据清理脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 显示将要清理的内容
echo -e "${YELLOW}⚠️  将删除以下数据：${NC}"
echo "  1. MySQL 数据库所有表数据（保留表结构）"
echo "  2. Redis 所有缓存数据"
echo "  3. 本地上传的代码仓库文件 (backend/data/repos)"
echo "  4. DeepWiki 临时文件 (deepwiki-open/data/uploads) - 约 312M"
echo "  5. RAG 向量数据库 (local-rag-service/chroma_data)"
echo "  6. 所有日志文件"
echo ""
echo -e "${YELLOW}预计释放空间: 约 337M${NC}"
echo ""

# 如果传入参数 --force 或 -f，则跳过确认
if [ "$1" != "--force" ] && [ "$1" != "-f" ]; then
    read -p "确认要继续吗？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${RED}❌ 操作已取消${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${GREEN}开始清理数据...${NC}"
echo ""

# ============================================
# 1. 清理 MySQL 数据库（保留表结构）
# ============================================
echo -e "${BLUE}[1/5] 清理 MySQL 数据库...${NC}"

# 检测 MySQL 连接方式（Docker 或直接连接）
if docker ps | grep -q mysql 2>/dev/null; then
    MYSQL_CMD="docker exec mysql mysql -uroot -p123456"
else
    MYSQL_CMD="mysql -h 127.0.0.1 -P 3306 -u root -p123456"
fi

# 显示清理前的数据量
repos_count=$($MYSQL_CMD -e "USE code_analysis; SELECT COUNT(*) FROM repositories;" 2>&1 | grep -v Warning | tail -1)
tasks_count=$($MYSQL_CMD -e "USE code_analysis; SELECT COUNT(*) FROM analysis_tasks;" 2>&1 | grep -v Warning | tail -1)
files_count=$($MYSQL_CMD -e "USE code_analysis; SELECT COUNT(*) FROM file_analyses;" 2>&1 | grep -v Warning | tail -1)

echo "  清理前数据量："
echo "    - repositories: $repos_count 条"
echo "    - analysis_tasks: $tasks_count 条"
echo "    - file_analyses: $files_count 条"
echo ""
echo "  开始清空表数据..."

# 直接使用 mysql 命令，避免变量展开问题
mysql -h 127.0.0.1 -P 3306 -u root -p123456 code_analysis -e "
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE file_analyses;
TRUNCATE TABLE analysis_tasks;
TRUNCATE TABLE repositories;
TRUNCATE TABLE task_readme;
TRUNCATE TABLE analysis_items;
SET FOREIGN_KEY_CHECKS = 1;
" 2>&1 | grep -v Warning > /dev/null

echo "  ✅ MySQL 数据已清空"
echo -e "${GREEN}✅ MySQL 数据库清理完成${NC}"
echo ""

# ============================================
# 2. 清理 Redis 缓存
# ============================================
echo -e "${BLUE}[2/5] 清理 Redis 缓存...${NC}"

# 尝试使用 Docker 命令，如果失败则尝试直接连接
if docker ps | grep -q redis 2>/dev/null; then
    docker exec redis redis-cli FLUSHALL > /dev/null 2>&1
elif command -v redis-cli &> /dev/null; then
    redis-cli FLUSHALL > /dev/null 2>&1
else
    echo "  ⚠️  未找到 Redis，跳过清理"
fi

echo -e "${GREEN}✅ Redis 缓存清理完成${NC}"
echo ""

# ============================================
# 3. 清理本地代码仓库文件
# ============================================
echo -e "${BLUE}[3/5] 清理本地代码仓库文件...${NC}"

# 清理 backend/data/repos
if [ -d "$BACKEND_DIR/data/repos" ]; then
    repos_count=$(ls -1 "$BACKEND_DIR/data/repos" 2>/dev/null | wc -l | tr -d ' ')
    repos_size=$(du -sh "$BACKEND_DIR/data/repos" 2>/dev/null | cut -f1)
    rm -rf "$BACKEND_DIR/data/repos"/*
    echo "  - 已清理: backend/data/repos ($repos_count 个仓库, $repos_size)"
fi

# 清理 deepwiki-open/data/uploads
DEEPWIKI_UPLOADS="$PROJECT_ROOT/deepwiki-open/data/uploads"
if [ -d "$DEEPWIKI_UPLOADS" ]; then
    uploads_count=$(ls -1 "$DEEPWIKI_UPLOADS" 2>/dev/null | wc -l | tr -d ' ')
    uploads_size=$(du -sh "$DEEPWIKI_UPLOADS" 2>/dev/null | cut -f1)
    echo "  - 正在清理: deepwiki-open/data/uploads ($uploads_count 个文件/目录, $uploads_size)..."
    rm -rf "$DEEPWIKI_UPLOADS"/*
    echo "  - ✅ 已清理: deepwiki-open/data/uploads (释放 $uploads_size 空间)"
fi

echo -e "${GREEN}✅ 本地代码仓库文件清理完成${NC}"
echo ""

# ============================================
# 4. 清理 RAG 向量数据库
# ============================================
echo -e "${BLUE}[4/5] 清理 RAG 向量数据库...${NC}"

# 检查 RAG 服务是否在运行（添加超时保护）
RAG_PID=$(timeout 3 lsof -ti:32421 2>/dev/null || echo "")
RAG_WAS_RUNNING=false

if [ ! -z "$RAG_PID" ]; then
    echo "  - 检测到 RAG 服务正在运行，先停止服务..."
    RAG_WAS_RUNNING=true
    kill -9 $RAG_PID 2>/dev/null || true
    sleep 2
    echo "  - RAG 服务已停止"
else
    echo "  - RAG 服务未运行"
fi

# 清理 local-rag-service/chroma_data
RAG_CHROMA_DATA="$PROJECT_ROOT/local-rag-service/chroma_data"
if [ -d "$RAG_CHROMA_DATA" ]; then
    # 显示清理前的大小
    if [ -f "$RAG_CHROMA_DATA/chroma.sqlite3" ]; then
        chroma_size=$(du -sh "$RAG_CHROMA_DATA" 2>/dev/null | cut -f1)
        sqlite_size=$(du -sh "$RAG_CHROMA_DATA/chroma.sqlite3" 2>/dev/null | cut -f1)
        echo "  - 清理前: local-rag-service/chroma_data ($chroma_size, sqlite: $sqlite_size)"
    fi

    # 删除所有内容，包括 chroma.sqlite3 和 UUID 目录
    rm -rf "$RAG_CHROMA_DATA"/*
    rm -rf "$RAG_CHROMA_DATA"/.* 2>/dev/null || true
    echo "  - ✅ 已清理: local-rag-service/chroma_data"
fi

# 清理 backend/data/chroma_data
BACKEND_CHROMA_DATA="$BACKEND_DIR/data/chroma_data"
if [ -d "$BACKEND_CHROMA_DATA" ]; then
    chroma_count=$(ls -1 "$BACKEND_CHROMA_DATA" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$chroma_count" -gt 0 ]; then
        rm -rf "$BACKEND_CHROMA_DATA"/*
        rm -rf "$BACKEND_CHROMA_DATA"/.* 2>/dev/null || true
        echo "  - ✅ 已清理: backend/data/chroma_data"
    fi
fi

# 如果 RAG 服务之前在运行，重新启动
if [ "$RAG_WAS_RUNNING" = true ]; then
    echo "  - 重新启动 RAG 服务..."
    cd "$PROJECT_ROOT/local-rag-service"
    nohup .venv/bin/python main.py > logs/rag.log 2>&1 &
    sleep 3
    NEW_RAG_PID=$(timeout 3 lsof -ti:32421 2>/dev/null || echo "")
    if [ ! -z "$NEW_RAG_PID" ]; then
        echo "  - RAG 服务已重启 (PID: $NEW_RAG_PID)"
    else
        echo "  - ⚠️  RAG 服务重启失败，请手动启动"
    fi
    cd "$PROJECT_ROOT"
fi

echo -e "${GREEN}✅ RAG 向量数据库清理完成${NC}"
echo ""

# ============================================
# 5. 清理日志文件
# ============================================
echo -e "${BLUE}[5/5] 清理日志文件...${NC}"

# 清理 backend 日志
if [ -d "$BACKEND_DIR/logs" ]; then
    log_count=$(ls -1 "$BACKEND_DIR/logs"/*.log 2>/dev/null | wc -l | tr -d ' ')
    if [ "$log_count" -gt 0 ]; then
        rm -f "$BACKEND_DIR/logs"/*.log
        echo "  - 已清理: backend/logs/*.log ($log_count 个文件)"
    else
        echo "  - backend/logs: 无日志文件"
    fi
fi

if [ -f "$BACKEND_DIR/uvicorn.log" ]; then
    log_size=$(du -sh "$BACKEND_DIR/uvicorn.log" 2>/dev/null | cut -f1)
    > "$BACKEND_DIR/uvicorn.log"
    echo "  - 已清空: backend/uvicorn.log (原大小: $log_size)"
fi

# 清理 Celery 日志
if [ -f "$BACKEND_DIR/celery.log" ]; then
    log_size=$(du -sh "$BACKEND_DIR/celery.log" 2>/dev/null | cut -f1)
    > "$BACKEND_DIR/celery.log"
    echo "  - 已清空: backend/celery.log (原大小: $log_size)"
fi

# 清理其他服务日志
for service_dir in "$PROJECT_ROOT/deepwiki-open" "$PROJECT_ROOT/local-rag-service"; do
    if [ -d "$service_dir/logs" ]; then
        log_count=$(ls -1 "$service_dir/logs"/*.log 2>/dev/null | wc -l | tr -d ' ')
        if [ "$log_count" -gt 0 ]; then
            rm -f "$service_dir/logs"/*.log
            echo "  - 已清理: $(basename $service_dir)/logs/*.log ($log_count 个文件)"
        fi
    fi
done

echo -e "${GREEN}✅ 日志文件清理完成${NC}"
echo ""

# ============================================
# 完成 - 验证清理结果
# ============================================
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   ✅ 所有数据清理完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

echo -e "${BLUE}验证清理结果：${NC}"
echo ""

# 验证 MySQL
if docker ps | grep -q mysql 2>/dev/null; then
    mysql_count=$(docker exec mysql mysql -uroot -p123456 -e "USE code_analysis; SELECT COUNT(*) FROM repositories;" 2>&1 | grep -v Warning | tail -1)
else
    mysql_count=$(mysql -h 127.0.0.1 -P 3306 -u root -p123456 -e "USE code_analysis; SELECT COUNT(*) FROM repositories;" 2>&1 | grep -v Warning | tail -1)
fi
echo "  MySQL repositories: $mysql_count 条记录"

# 验证 Redis
if docker ps | grep -q redis 2>/dev/null; then
    redis_keys=$(docker exec redis redis-cli DBSIZE 2>/dev/null | grep -oE '[0-9]+')
elif command -v redis-cli &> /dev/null; then
    redis_keys=$(redis-cli DBSIZE 2>/dev/null | grep -oE '[0-9]+')
else
    redis_keys="N/A"
fi
echo "  Redis 键数量: $redis_keys"

# 验证本地文件
repos_count=$(ls -1 "$BACKEND_DIR/data/repos" 2>/dev/null | wc -l | tr -d ' ')
echo "  backend/data/repos: $repos_count 个仓库"

uploads_count=$(ls -1 "$PROJECT_ROOT/deepwiki-open/data/uploads" 2>/dev/null | wc -l | tr -d ' ')
echo "  deepwiki-open/data/uploads: $uploads_count 个文件"

# 验证 ChromaDB
if [ -f "$PROJECT_ROOT/local-rag-service/chroma_data/chroma.sqlite3" ]; then
    chroma_size=$(du -sh "$PROJECT_ROOT/local-rag-service/chroma_data/chroma.sqlite3" 2>/dev/null | cut -f1)
    echo "  ChromaDB: $chroma_size (⚠️ 未完全清空)"
else
    echo "  ChromaDB: 已清空 ✅"
fi

echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "  - 现在可以重新上传代码进行分析了"
echo "  - Embedding 模型: 阿里云 DashScope text-embedding-v4 (1024维)"
echo "  - Batch size: 10 (local-rag-service 和 deepwiki-open 已统一)"
echo "  - 向量维度与 deepwiki-open 完全一致"
echo ""

