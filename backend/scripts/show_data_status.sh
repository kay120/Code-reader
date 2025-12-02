#!/bin/bash

# ============================================
# 数据状态查看脚本
# 功能：显示当前系统中的数据状态
# ============================================

# 颜色定义
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
echo -e "${BLUE}   Code-reader 数据状态${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================
# 1. MySQL 数据库状态
# ============================================
echo -e "${BLUE}[1] MySQL 数据库状态${NC}"
echo ""

docker exec mysql mysql -uroot -p123456 << 'EOF' 2>&1 | grep -v Warning
USE code_analysis;

SELECT 
    '仓库数量' as 项目,
    COUNT(*) as 数量
FROM repositories
UNION ALL
SELECT 
    '分析任务数量' as 项目,
    COUNT(*) as 数量
FROM analysis_tasks
UNION ALL
SELECT 
    '文件分析记录数量' as 项目,
    COUNT(*) as 数量
FROM file_analyses
UNION ALL
SELECT 
    '分析项数量' as 项目,
    COUNT(*) as 数量
FROM analysis_items
UNION ALL
SELECT 
    'README 数量' as 项目,
    COUNT(*) as 数量
FROM task_readmes;

SELECT '---' as '---', '---' as '---';

SELECT 
    status as 任务状态,
    COUNT(*) as 数量
FROM analysis_tasks
GROUP BY status;
EOF

echo ""

# ============================================
# 2. Redis 状态
# ============================================
echo -e "${BLUE}[2] Redis 缓存状态${NC}"
echo ""

redis_keys=$(docker exec redis redis-cli DBSIZE 2>/dev/null | grep -oE '[0-9]+')
echo "  Redis 键数量: $redis_keys"

queue_size=$(docker exec redis redis-cli LLEN analysis 2>/dev/null)
echo "  分析队列长度: $queue_size"

echo ""

# ============================================
# 3. 本地文件状态
# ============================================
echo -e "${BLUE}[3] 本地文件状态${NC}"
echo ""

# 统计 backend/data/repos（使用 ls 代替 find，更快）
repos_count=0
repos_size=0
if [ -d "$BACKEND_DIR/data/repos" ]; then
    repos_count=$(ls -1 "$BACKEND_DIR/data/repos" 2>/dev/null | wc -l | tr -d ' ')
    repos_size=$(du -sh "$BACKEND_DIR/data/repos" 2>/dev/null | cut -f1)
fi
echo "  backend/data/repos: $repos_count 个仓库, 大小: $repos_size"

# 统计 deepwiki-open/data/uploads（快速统计，不计算大小）
uploads_count=0
if [ -d "$PROJECT_ROOT/deepwiki-open/data/uploads" ]; then
    uploads_count=$(ls -1 "$PROJECT_ROOT/deepwiki-open/data/uploads" 2>/dev/null | wc -l | tr -d ' ')
fi
echo "  deepwiki-open/data/uploads: $uploads_count 个文件/目录"

echo ""

# ============================================
# 4. RAG 向量数据库状态
# ============================================
echo -e "${BLUE}[4] RAG 向量数据库状态${NC}"
echo ""

# 检查 RAG 服务状态
rag_pid=$(lsof -ti:32421 2>/dev/null)
if [ ! -z "$rag_pid" ]; then
    echo "  RAG 服务状态: 运行中 (PID: $rag_pid)"
else
    echo "  RAG 服务状态: 未运行"
fi
echo ""

# local-rag-service/chroma_data
rag_size=0
rag_file_count=0
if [ -d "$PROJECT_ROOT/local-rag-service/chroma_data" ]; then
    rag_size=$(du -sh "$PROJECT_ROOT/local-rag-service/chroma_data" 2>/dev/null | cut -f1)
    rag_file_count=$(ls -1 "$PROJECT_ROOT/local-rag-service/chroma_data" 2>/dev/null | wc -l | tr -d ' ')

    # 检查是否有 chroma.sqlite3
    if [ -f "$PROJECT_ROOT/local-rag-service/chroma_data/chroma.sqlite3" ]; then
        sqlite_size=$(du -sh "$PROJECT_ROOT/local-rag-service/chroma_data/chroma.sqlite3" 2>/dev/null | cut -f1)
        echo "  local-rag-service/chroma_data: $rag_size (文件数: $rag_file_count)"
        echo "    - chroma.sqlite3: $sqlite_size"
    else
        echo "  local-rag-service/chroma_data: $rag_size (文件数: $rag_file_count, 无数据)"
    fi
else
    echo "  local-rag-service/chroma_data: 目录不存在"
fi

# backend/data/chroma_data
backend_chroma_size=0
backend_file_count=0
if [ -d "$BACKEND_DIR/data/chroma_data" ]; then
    backend_chroma_size=$(du -sh "$BACKEND_DIR/data/chroma_data" 2>/dev/null | cut -f1)
    backend_file_count=$(ls -1 "$BACKEND_DIR/data/chroma_data" 2>/dev/null | wc -l | tr -d ' ')
    echo "  backend/data/chroma_data: $backend_chroma_size (文件数: $backend_file_count)"
else
    echo "  backend/data/chroma_data: 目录不存在"
fi

echo ""

# ============================================
# 5. 日志文件状态
# ============================================
echo -e "${BLUE}[5] 日志文件状态${NC}"
echo ""

# backend 日志
backend_logs_count=0
backend_logs_size=0
if [ -d "$BACKEND_DIR/logs" ]; then
    backend_logs_count=$(find "$BACKEND_DIR/logs" -name "*.log" 2>/dev/null | wc -l | tr -d ' ')
    backend_logs_size=$(du -sh "$BACKEND_DIR/logs" 2>/dev/null | cut -f1)
fi
echo "  backend/logs: $backend_logs_count 个日志文件, 大小: $backend_logs_size"

# uvicorn.log
uvicorn_size=0
if [ -f "$BACKEND_DIR/uvicorn.log" ]; then
    uvicorn_size=$(du -sh "$BACKEND_DIR/uvicorn.log" 2>/dev/null | cut -f1)
fi
echo "  backend/uvicorn.log: $uvicorn_size"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   数据状态查看完成${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${YELLOW}💡 提示：运行 ./clean_data.sh 可以清理所有数据${NC}"

