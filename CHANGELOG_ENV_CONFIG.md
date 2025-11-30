# 环境变量配置优化 - 修改日志

## 修改日期
2025-11-30

## 修改概述
优化了环境变量配置管理，将配置文件分离到 backend 和 frontend 目录，并修复了 Celery Worker 环境变量加载问题。

## 主要修改

### 1. 环境变量配置分离

**问题：**
- 原来所有环境变量都在根目录的 `.env` 文件中
- Backend 和 Frontend 的配置混在一起，不够清晰

**解决方案：**
- 创建 `backend/.env` 和 `backend/.env.example` - 存放后端相关配置
- 创建 `frontend/.env` 和 `frontend/.env.example` - 存放前端相关配置
- 删除根目录的 `.env` 和 `.env.example` 文件

**新增文件：**
- `backend/.env.example` - Backend 环境变量模板
- `frontend/.env.example` - Frontend 环境变量模板

### 2. Celery Worker 并发配置

**问题：**
- Celery Worker 默认并发数为 10，导致电脑卡顿

**解决方案：**
- 在 `backend/.env` 中添加 `CELERY_WORKER_CONCURRENCY=2` 配置
- 修改 `backend/celery_app.py`，从环境变量读取并发数配置

**修改文件：**
- `backend/celery_app.py` - 添加环境变量读取逻辑

### 3. Celery Worker 环境变量加载修复

**问题：**
- Celery Worker 子进程无法读取环境变量（OPENAI_API_KEY 等）
- 导致任务执行时报错：`Missing required environment variables`

**解决方案：**
- 在 `celery_app.py` 中指定 `.env` 文件的完整路径
- 在 worker 子进程初始化时重新加载环境变量

**关键代码修改：**
```python
# 主进程加载环境变量
backend_dir = Path(__file__).parent.absolute()
env_path = backend_dir / '.env'
load_dotenv(env_path)

# 子进程初始化时重新加载
@worker_process_init.connect
def init_worker_process(**kwargs):
    backend_dir = Path(__file__).parent.absolute()
    env_path = backend_dir / '.env'
    load_dotenv(env_path, override=True)
```

### 4. Backend 环境变量配置项

`backend/.env` 包含以下配置：

**应用配置：**
- `APP_HOST` - 应用主机地址
- `APP_PORT` - 应用端口

**数据库配置：**
- `DB_DIALECT`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `DB_PARAMS`, `DB_ECHO`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`

**OpenAI API 配置：**
- `OPENAI_API_KEY` - API 密钥
- `OPENAI_BASE_URL` - API 地址
- `OPENAI_MODEL` - 模型名称

**LLM 配置：**
- `LLM_MAX_CONCURRENT`, `LLM_BATCH_SIZE`, `LLM_REQUEST_TIMEOUT`, `LLM_RETRY_DELAY`

**RAG 配置：**
- `RAG_BASE_URL`, `RAG_BATCH_SIZE`

**API 配置：**
- `API_BASE_URL`, `README_API_BASE_URL`, `CLAUDE_CHAT_API_BASE_URL`

**存储路径：**
- `LOCAL_REPO_PATH`, `RESULTS_PATH`, `VECTORSTORE_PATH`

**Celery 配置：**
- `CELERY_WORKER_CONCURRENCY` - Worker 并发数
- `CELERY_BROKER_URL` - Redis 消息代理地址
- `CELERY_RESULT_BACKEND` - Redis 结果后端地址

**其他：**
- `GITHUB_TOKEN`, `PASSWORD`

## 测试验证

### 1. 环境变量加载测试
创建了 `test_env_vars.py` 脚本验证环境变量是否正确加载：
```bash
python3 test_env_vars.py
```

### 2. Celery Worker 测试
- 重启 Celery Worker 后，并发数正确设置为 2
- Worker 子进程能够正确读取 OPENAI_API_KEY 等环境变量
- 任务执行不再报错 "Missing required environment variables"

## 影响范围

**受影响的组件：**
- Celery Worker - 环境变量加载方式改变
- Backend API - 配置文件路径改变
- Frontend - 配置文件路径改变

**不受影响的组件：**
- 数据库结构
- API 接口
- 前端功能

## 迁移指南

如果其他开发者需要更新代码：

1. 删除根目录的 `.env` 文件（如果存在）
2. 复制 `backend/.env.example` 为 `backend/.env`
3. 复制 `frontend/.env.example` 为 `frontend/.env`
4. 根据实际情况修改配置值
5. 重启 Backend 和 Celery Worker 服务

## 相关文件

**新增：**
- `backend/.env.example`
- `frontend/.env.example`
- `backend/celery_app.py`（环境变量加载逻辑）

**修改：**
- `backend/celery_app.py`（添加环境变量加载）

**删除：**
- `.env.example`（根目录）

## 备注

- `.env` 文件已添加到 `.gitignore`，不会提交到版本库
- 只提交 `.env.example` 模板文件
- 开发者需要根据模板创建自己的 `.env` 文件

