#!/bin/bash

# ============================================
# ChromaDB 数据清理脚本（测试用）
# 功能：只清理 ChromaDB 向量数据库
# ============================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
CODE_READER_ROOT="$(dirname "$BACKEND_DIR")"
PROJECT_ROOT="$(dirname "$CODE_READER_ROOT")"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   ChromaDB 数据清理脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 显示当前 ChromaDB 状态
echo -e "${YELLOW}当前 ChromaDB 状态：${NC}"
echo ""

RAG_CHROMA_DATA="$PROJECT_ROOT/local-rag-service/chroma_data"
if [ -d "$RAG_CHROMA_DATA" ]; then
    echo "local-rag-service/chroma_data:"
    du -sh "$RAG_CHROMA_DATA" 2>/dev/null || echo "  无法读取大小"
    ls -1 "$RAG_CHROMA_DATA" 2>/dev/null | head -5
    file_count=$(ls -1 "$RAG_CHROMA_DATA" 2>/dev/null | wc -l | tr -d ' ')
    echo "  文件/目录数量: $file_count"
fi

echo ""

# 确认操作
read -p "确认要清理 ChromaDB 数据吗？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}❌ 操作已取消${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}开始清理 ChromaDB...${NC}"
echo ""

# 检查 RAG 服务是否在运行
RAG_PID=$(lsof -ti:32421 2>/dev/null)
RAG_WAS_RUNNING=false

if [ ! -z "$RAG_PID" ]; then
    echo "  - 检测到 RAG 服务正在运行 (PID: $RAG_PID)"
    echo "  - 停止 RAG 服务..."
    RAG_WAS_RUNNING=true
    kill -9 $RAG_PID 2>/dev/null || true
    sleep 2
    echo "  - ✅ RAG 服务已停止"
fi

echo ""

# 清理 local-rag-service/chroma_data
if [ -d "$RAG_CHROMA_DATA" ]; then
    echo "  - 清理 local-rag-service/chroma_data..."
    
    # 显示清理前的大小
    before_size=$(du -sh "$RAG_CHROMA_DATA" 2>/dev/null | cut -f1)
    echo "    清理前大小: $before_size"
    
    # 删除所有内容
    rm -rf "$RAG_CHROMA_DATA"/*
    rm -rf "$RAG_CHROMA_DATA"/.* 2>/dev/null || true
    
    # 显示清理后的大小
    after_size=$(du -sh "$RAG_CHROMA_DATA" 2>/dev/null | cut -f1)
    echo "    清理后大小: $after_size"
    echo "  - ✅ 已清理: local-rag-service/chroma_data"
fi

echo ""

# 清理 backend/data/chroma_data
BACKEND_CHROMA_DATA="$BACKEND_DIR/data/chroma_data"
if [ -d "$BACKEND_CHROMA_DATA" ]; then
    echo "  - 清理 backend/data/chroma_data..."
    rm -rf "$BACKEND_CHROMA_DATA"/*
    rm -rf "$BACKEND_CHROMA_DATA"/.* 2>/dev/null || true
    echo "  - ✅ 已清理: backend/data/chroma_data"
fi

echo ""

# 如果 RAG 服务之前在运行，重新启动
if [ "$RAG_WAS_RUNNING" = true ]; then
    echo "  - 重新启动 RAG 服务..."
    cd "$PROJECT_ROOT/local-rag-service"
    nohup .venv/bin/python main.py > logs/rag.log 2>&1 &
    sleep 3
    
    NEW_RAG_PID=$(lsof -ti:32421 2>/dev/null)
    if [ ! -z "$NEW_RAG_PID" ]; then
        echo "  - ✅ RAG 服务已重启 (PID: $NEW_RAG_PID)"
    else
        echo -e "  - ${YELLOW}⚠️  RAG 服务重启失败，请手动启动${NC}"
    fi
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   ✅ ChromaDB 清理完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# 显示清理后的状态
echo -e "${YELLOW}清理后 ChromaDB 状态：${NC}"
echo ""

if [ -d "$RAG_CHROMA_DATA" ]; then
    echo "local-rag-service/chroma_data:"
    du -sh "$RAG_CHROMA_DATA" 2>/dev/null || echo "  无法读取大小"
    file_count=$(ls -1 "$RAG_CHROMA_DATA" 2>/dev/null | wc -l | tr -d ' ')
    echo "  文件/目录数量: $file_count"
fi

