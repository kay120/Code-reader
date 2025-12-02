# 数据清理脚本使用说明

## 📋 脚本说明

`clean_all_data.sh` - 完整数据清理脚本

**功能：**
- 清空 MySQL 数据库所有表数据（保留表结构）
- 清空 Redis 所有缓存数据
- 删除本地上传的代码仓库文件
- 删除 RAG 向量数据库
- 清理所有日志文件

**特点：**
- ✅ 保留数据库表结构
- ✅ 安全确认机制
- ✅ 彩色输出，清晰易读
- ✅ 错误自动停止

---

## 🚀 使用方法

### 方法 1：直接执行（推荐）

```bash
cd /Users/kay/code/work/codereader_workspace/Code-reader/backend
./scripts/clean_all_data.sh
```

### 方法 2：使用 bash 执行

```bash
cd /Users/kay/code/work/codereader_workspace/Code-reader/backend
bash scripts/clean_all_data.sh
```

---

## 📝 执行流程

1. **显示警告信息**
   ```
   ⚠️  警告：此操作将删除以下数据：
     1. MySQL 数据库所有表数据（保留表结构）
     2. Redis 所有缓存数据
     3. 本地上传的代码仓库文件
     4. RAG 向量数据库
     5. 所有日志文件
   ```

2. **确认操作**
   ```
   确认要继续吗？(yes/no):
   ```
   - 输入 `yes` 继续
   - 输入 `no` 或其他任何内容取消

3. **执行清理**
   - [1/5] 清理 MySQL 数据库
   - [2/5] 清理 Redis 缓存
   - [3/5] 清理本地代码仓库文件
   - [4/5] 清理 RAG 向量数据库
   - [5/5] 清理日志文件

4. **显示完成摘要**

---

## 📂 清理的目录和文件

### MySQL 数据库表
- `file_analyses` - 文件分析记录
- `analysis_tasks` - 分析任务
- `repositories` - 仓库信息
- `task_readmes` - 任务 README
- `analysis_items` - 分析项

### Redis
- 所有缓存数据（FLUSHALL）

### 本地文件
- `backend/data/repos/*` - 上传的代码仓库
- `deepwiki-open/data/uploads/*` - README API 上传文件
- `local-rag-service/chroma_data/*` - RAG 向量数据库
- `backend/data/chroma_data/*` - 后端向量数据库

### 日志文件
- `backend/logs/*.log` - 后端日志
- `backend/uvicorn.log` - Uvicorn 日志
- `deepwiki-open/logs/*.log` - DeepWiki 日志
- `local-rag-service/logs/*.log` - RAG 服务日志

---

## ⚠️ 注意事项

1. **数据不可恢复**
   - 清理后的数据无法恢复，请谨慎操作
   - 如需备份，请在执行前手动备份

2. **服务状态**
   - 建议在清理前停止所有服务
   - 清理后需要重新启动服务

3. **权限要求**
   - 需要有 Docker 容器访问权限
   - 需要有文件系统写权限

---

## 🔧 故障排除

### 问题 1：权限不足

**错误：**
```
Permission denied
```

**解决：**
```bash
chmod +x scripts/clean_all_data.sh
```

### 问题 2：Docker 容器未运行

**错误：**
```
Error: No such container: mysql
```

**解决：**
```bash
# 启动 MySQL 容器
docker start mysql

# 启动 Redis 容器
docker start redis
```

### 问题 3：数据库连接失败

**错误：**
```
ERROR 2002 (HY000): Can't connect to MySQL server
```

**解决：**
```bash
# 检查 MySQL 容器状态
docker ps | grep mysql

# 重启 MySQL 容器
docker restart mysql
```

---

## 📊 清理后的状态

执行成功后，系统将处于以下状态：

- ✅ 数据库表结构完整，数据为空
- ✅ Redis 缓存为空
- ✅ 本地文件目录为空
- ✅ 日志文件为空或已删除
- ✅ 系统可以立即接受新的上传

---

## 💡 使用场景

1. **开发测试**
   - 清理测试数据
   - 重新开始测试

2. **问题排查**
   - 清除异常数据
   - 重现问题

3. **定期维护**
   - 清理过期数据
   - 释放存储空间

4. **版本升级**
   - 清理旧版本数据
   - 准备新版本测试

---

## 🔗 相关命令

### 只清理数据库
```bash
docker exec mysql mysql -uroot -p123456 -e "
USE code_analysis;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE file_analyses;
TRUNCATE TABLE analysis_tasks;
TRUNCATE TABLE repositories;
TRUNCATE TABLE task_readmes;
TRUNCATE TABLE analysis_items;
SET FOREIGN_KEY_CHECKS = 1;
"
```

### 只清理 Redis
```bash
docker exec redis redis-cli FLUSHALL
```

### 只清理文件
```bash
rm -rf backend/data/repos/*
rm -rf deepwiki-open/data/uploads/*
```

### 只清理日志
```bash
rm -f backend/logs/*.log
> backend/uvicorn.log
```

