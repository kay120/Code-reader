#!/bin/bash

# Code-reader 残留文件清理脚本
# 用于清理删除项目后的残留文件

set -e

echo "========================================"
echo "  Code-reader 残留文件清理工具"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
REPOS_DIR="$BACKEND_DIR/data/repos"
DEEPWIKI_DATA_DIR="$SCRIPT_DIR/../deepwiki-open/data"
CHROMA_DATA_DIR="$SCRIPT_DIR/../local-rag-service/chroma_data"

echo -e "${BLUE}[1/5] 检查残留文件...${NC}"
echo ""

# 检查 repos 目录
if [ -d "$REPOS_DIR" ]; then
    REPO_COUNT=$(find "$REPOS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    REPO_SIZE=$(du -sh "$REPOS_DIR" 2>/dev/null | cut -f1)
    
    echo -e "📁 上传的代码仓库目录: ${YELLOW}$REPOS_DIR${NC}"
    echo -e "   - 目录数量: ${YELLOW}$REPO_COUNT${NC} 个"
    echo -e "   - 占用空间: ${YELLOW}$REPO_SIZE${NC}"
    echo ""
    
    if [ "$REPO_COUNT" -gt 0 ]; then
        echo "   目录列表:"
        find "$REPOS_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | while read dir; do
            size=$(du -sh "$REPOS_DIR/$dir" 2>/dev/null | cut -f1)
            echo "   - $dir ($size)"
        done
        echo ""
    fi
else
    echo -e "${GREEN}✅ 上传的代码仓库目录不存在${NC}"
    echo ""
fi

# 检查 deepwiki data 目录
if [ -d "$DEEPWIKI_DATA_DIR" ]; then
    DEEPWIKI_SIZE=$(du -sh "$DEEPWIKI_DATA_DIR" 2>/dev/null | cut -f1)
    DEEPWIKI_FILES=$(find "$DEEPWIKI_DATA_DIR" -type f ! -name "README.md" | wc -l | tr -d ' ')

    echo -e "📁 deepwiki 数据目录: ${YELLOW}$DEEPWIKI_DATA_DIR${NC}"
    echo -e "   - 文件数量: ${YELLOW}$DEEPWIKI_FILES${NC} 个"
    echo -e "   - 占用空间: ${YELLOW}$DEEPWIKI_SIZE${NC}"
    echo ""
else
    echo -e "${GREEN}✅ deepwiki 数据目录不存在${NC}"
    echo ""
fi

# 检查向量数据库目录
if [ -d "$CHROMA_DATA_DIR" ]; then
    CHROMA_SIZE=$(du -sh "$CHROMA_DATA_DIR" 2>/dev/null | cut -f1)
    CHROMA_COLLECTIONS=$(find "$CHROMA_DATA_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    CHROMA_DB_SIZE=$(du -sh "$CHROMA_DATA_DIR/chroma.sqlite3" 2>/dev/null | cut -f1 || echo "0B")

    echo -e "📁 向量数据库目录: ${YELLOW}$CHROMA_DATA_DIR${NC}"
    echo -e "   - 向量集合数量: ${YELLOW}$CHROMA_COLLECTIONS${NC} 个"
    echo -e "   - 数据库大小: ${YELLOW}$CHROMA_DB_SIZE${NC}"
    echo -e "   - 总占用空间: ${YELLOW}$CHROMA_SIZE${NC}"
    echo ""

    if [ "$CHROMA_COLLECTIONS" -gt 0 ]; then
        echo "   集合列表:"
        find "$CHROMA_DATA_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | while read dir; do
            size=$(du -sh "$CHROMA_DATA_DIR/$dir" 2>/dev/null | cut -f1)
            echo "   - $dir ($size)"
        done
        echo ""
    fi
else
    echo -e "${GREEN}✅ 向量数据库目录不存在${NC}"
    echo ""
fi

# 计算总占用空间
TOTAL_SIZE=0
if [ -d "$REPOS_DIR" ]; then
    REPOS_KB=$(du -sk "$REPOS_DIR" 2>/dev/null | cut -f1)
    TOTAL_SIZE=$((TOTAL_SIZE + REPOS_KB))
fi
if [ -d "$DEEPWIKI_DATA_DIR" ]; then
    DEEPWIKI_KB=$(du -sk "$DEEPWIKI_DATA_DIR" 2>/dev/null | cut -f1)
    TOTAL_SIZE=$((TOTAL_SIZE + DEEPWIKI_KB))
fi
if [ -d "$CHROMA_DATA_DIR" ]; then
    CHROMA_KB=$(du -sk "$CHROMA_DATA_DIR" 2>/dev/null | cut -f1)
    TOTAL_SIZE=$((TOTAL_SIZE + CHROMA_KB))
fi

TOTAL_MB=$((TOTAL_SIZE / 1024))

echo -e "${BLUE}[2/5] 统计信息${NC}"
echo -e "   总占用空间: ${YELLOW}${TOTAL_MB}MB${NC}"
echo ""

# 询问是否清理
if [ "$TOTAL_SIZE" -eq 0 ]; then
    echo -e "${GREEN}✅ 没有发现残留文件，无需清理${NC}"
    exit 0
fi

echo -e "${BLUE}[3/5] 确认清理${NC}"
echo -e "${RED}警告: 此操作将删除所有残留文件，无法恢复！${NC}"
echo ""
echo -e "${YELLOW}将清理以下内容:${NC}"
if [ -d "$REPOS_DIR" ] && [ "$REPO_COUNT" -gt 0 ]; then
    echo -e "  - 代码仓库: $REPO_COUNT 个目录"
fi
if [ -d "$DEEPWIKI_DATA_DIR" ] && [ "$DEEPWIKI_FILES" -gt 0 ]; then
    echo -e "  - deepwiki 数据: $DEEPWIKI_FILES 个文件"
fi
if [ -d "$CHROMA_DATA_DIR" ] && [ "$CHROMA_COLLECTIONS" -gt 0 ]; then
    echo -e "  - 向量数据库: $CHROMA_COLLECTIONS 个集合 + 数据库文件"
fi
echo ""
read -p "是否继续清理? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}已取消清理操作${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}[4/5] 检查 RAG 服务状态...${NC}"
echo ""

# 检查 RAG 服务是否运行
RAG_PID=$(lsof -ti:32421 2>/dev/null)
if [ -n "$RAG_PID" ]; then
    echo -e "${YELLOW}⚠️  检测到 RAG 服务正在运行 (PID: $RAG_PID)${NC}"
    echo -e "${YELLOW}   需要停止服务才能清理向量数据库${NC}"
    echo ""
    read -p "是否停止 RAG 服务? (yes/no): " stop_rag

    if [ "$stop_rag" = "yes" ]; then
        echo -e "🛑 停止 RAG 服务..."
        kill $RAG_PID 2>/dev/null
        sleep 2
        echo -e "${GREEN}✅ RAG 服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  跳过向量数据库清理${NC}"
        SKIP_CHROMA=true
    fi
else
    echo -e "${GREEN}✅ RAG 服务未运行，可以安全清理${NC}"
    SKIP_CHROMA=false
fi

echo ""
echo -e "${BLUE}[5/5] 开始清理...${NC}"
echo ""

# 清理 repos 目录
if [ -d "$REPOS_DIR" ] && [ "$REPO_COUNT" -gt 0 ]; then
    echo -e "🗑️  清理上传的代码仓库..."
    rm -rf "$REPOS_DIR"/*
    mkdir -p "$REPOS_DIR"
    echo -e "${GREEN}✅ 已清理 $REPO_COUNT 个目录${NC}"
fi

# 清理 deepwiki data 目录
if [ -d "$DEEPWIKI_DATA_DIR" ] && [ "$DEEPWIKI_FILES" -gt 0 ]; then
    echo -e "🗑️  清理 deepwiki 数据文件..."
    find "$DEEPWIKI_DATA_DIR" -type f ! -name "README.md" -delete
    echo -e "${GREEN}✅ 已清理 $DEEPWIKI_FILES 个文件${NC}"
fi

# 清理向量数据库
if [ -d "$CHROMA_DATA_DIR" ] && [ "$CHROMA_COLLECTIONS" -gt 0 ] && [ "$SKIP_CHROMA" != "true" ]; then
    echo -e "🗑️  清理向量数据库..."
    # 删除所有集合目录
    find "$CHROMA_DATA_DIR" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
    # 删除数据库文件
    rm -f "$CHROMA_DATA_DIR/chroma.sqlite3"
    echo -e "${GREEN}✅ 已清理 $CHROMA_COLLECTIONS 个向量集合 + 数据库文件${NC}"
    echo -e "${YELLOW}💡 提示: 请重启 RAG 服务以重新初始化数据库${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  清理完成! 释放空间: ${TOTAL_MB}MB${NC}"
echo -e "${GREEN}========================================${NC}"

