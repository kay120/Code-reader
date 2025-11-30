# 仓库删除功能升级说明

## 📋 概述

升级了 `delete_repository` 方法，现在删除项目时会**完全清理所有相关数据**，包括：
- ✅ MySQL 数据库记录
- ✅ 上传的项目源代码文件
- ✅ ChromaDB 向量数据库
- ✅ DeepWiki 生成的文档

## 🔧 修改的文件

### 1. `Code-reader/backend/services.py`
**修改位置**: 第 1539-1680 行 (`delete_repository` 方法)

**新增功能**:
1. 删除向量数据库（ChromaDB collections）
   - 获取仓库的所有分析任务
   - 提取 `task_index` 列表
   - 调用 RAG 服务 API 删除对应的 collections

2. 删除 DeepWiki 生成的文档
   - 从 `local_path` 提取 MD5 hash
   - 删除 `deepwiki-open/data/uploads/{hash}` 目录

3. 详细的删除报告
   - 返回 `deleted_items` 列表
   - 记录每一项清理的内容

### 2. `local-rag-service/main.py`
**新增 API 端点**:

#### DELETE `/collections/{collection_name}`
删除指定的向量数据库 collection

**参数**:
- `collection_name`: collection 名称（通常是 `task_index`）

**返回**:
```json
{
  "status": "success",
  "message": "Collection 'xxx' deleted successfully",
  "collection_name": "xxx"
}
```

**特性**:
- 幂等性：如果 collection 不存在，也返回成功
- 自动清理索引信息

#### GET `/collections`
列出所有 collections

**返回**:
```json
{
  "status": "success",
  "collections": [
    {
      "name": "index_xxx",
      "count": 53,
      "metadata": {"created_at": "2025-11-21T15:20:17"}
    }
  ],
  "total": 2
}
```

## 📊 删除流程

### 硬删除 (`soft_delete=false`)

```
1. 查询仓库记录
   ↓
2. 获取所有分析任务的 task_index
   ↓
3. 删除数据库记录（级联删除相关表）
   ↓
4. 删除上传的代码文件 (local_path)
   ↓
5. 删除向量数据库 collections
   - 遍历 task_index 列表
   - 调用 RAG 服务 DELETE /collections/{task_index}
   ↓
6. 删除 DeepWiki 文档
   - 提取 MD5 hash from local_path
   - 删除 deepwiki-open/data/uploads/{hash}
   ↓
7. 返回详细的删除报告
```

### 软删除 (`soft_delete=true`)

只设置 `repository.status = 0`，不删除任何文件或向量数据。

## 🧪 测试

运行测试脚本验证删除功能：

```bash
cd Code-reader/backend
python test_delete_repository.py
```

测试脚本会：
1. 列出所有仓库
2. 显示第一个仓库的信息
3. 显示该仓库的分析任务
4. 显示当前的 collections
5. 执行删除（需要确认）
6. 验证删除结果

## 📝 API 使用示例

### 删除仓库（完全清理）

```bash
curl -X DELETE "http://localhost:8000/api/repository/repositories/123?soft_delete=false"
```

**响应**:
```json
{
  "status": "success",
  "message": "仓库已完全删除，清理了 3 项数据",
  "repository_id": 123,
  "delete_type": "hard",
  "deleted_repository": {...},
  "deleted_items": [
    "代码文件: ./data/repos/abc123",
    "向量数据库: index_1763709617501",
    "DeepWiki文档: ../deepwiki-open/data/uploads/abc123"
  ]
}
```

### 查看所有向量数据库

```bash
curl "http://localhost:32421/collections"
```

### 手动删除向量数据库

```bash
curl -X DELETE "http://localhost:32421/collections/index_1763709617501"
```

## ⚠️ 注意事项

1. **硬删除不可恢复**
   - 所有数据将被永久删除
   - 建议在删除前做好备份

2. **级联删除**
   - 删除仓库会自动删除：
     - `analysis_tasks` 表中的任务记录
     - `file_analyses` 表中的文件分析记录
     - `analysis_items` 表中的分析项
     - `task_readmes` 表中的 README 内容

3. **错误处理**
   - 如果某一项清理失败，会记录警告日志
   - 不会影响其他项的清理
   - 最终仍会返回成功状态

4. **DeepWiki 文档路径**
   - 假设路径格式为 `./data/repos/{hash}`
   - DeepWiki 文档在 `../deepwiki-open/data/uploads/{hash}`
   - 如果路径格式不同，可能需要调整代码

## 🔄 服务重启

修改后需要重启以下服务：

```bash
# 重启 RAG 服务
cd local-rag-service
pkill -f "python.*main.py"
nohup python main.py > logs/rag.log 2>&1 &

# 重启后端服务
cd Code-reader/backend
lsof -ti:8000 | xargs kill -9
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > logs/backend.log 2>&1 &
```

## ✅ 验证清单

- [x] 修改 `services.py` 的 `delete_repository` 方法
- [x] 添加向量数据库删除逻辑
- [x] 添加 DeepWiki 文档删除逻辑
- [x] 在 RAG 服务中添加 DELETE `/collections/{name}` 端点
- [x] 在 RAG 服务中添加 GET `/collections` 端点
- [x] 创建测试脚本
- [x] 重启 RAG 服务
- [x] 重启后端服务
- [x] 验证 API 端点正常工作

## 📚 相关文件

- `Code-reader/backend/services.py` - 仓库服务（删除逻辑）
- `Code-reader/backend/routers.py` - API 路由
- `local-rag-service/main.py` - RAG 服务（向量数据库管理）
- `Code-reader/frontend/src/components/ProjectCard.tsx` - 前端删除调用

