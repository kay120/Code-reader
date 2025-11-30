# Celery 后台任务队列配置说明

## 📋 概述

Code Reader 使用 **Celery + Redis** 实现后台异步任务处理,避免长时间运行的分析任务阻塞 API 请求。

## 🎯 为什么需要 Celery?

### 问题
在没有 Celery 之前,代码分析任务直接在 FastAPI worker 进程中执行:
- 分析一个项目需要 5-30 分钟
- 期间会调用大量 LLM API (每个文件 1-3 秒)
- 占用 worker 进程资源,导致其他 API 请求变慢
- **结果**: 20-30% 的 API 请求响应时间超过 1-10 秒

### 解决方案
使用 Celery 将耗时任务移到独立的 worker 进程:
- FastAPI workers: 专门处理 API 请求 (响应时间 20-50ms)
- Celery workers: 专门处理分析任务 (不影响 API)
- **结果**: 100% 的 API 请求响应时间在 20-52ms 范围内 ✅

## 🛠️ 架构

```
用户请求 → FastAPI (12 workers)
              ↓ (立即返回)
         Redis 消息队列
              ↓
         Celery Workers (4个)
              ↓
         执行分析任务
```

## 📦 依赖服务

### 1. Redis
- **作用**: 消息代理 (broker) 和结果存储 (backend)
- **端口**: 6379
- **安装**: 使用 Docker (推荐)

### 2. Celery
- **作用**: 分布式任务队列
- **版本**: 5.3.0+
- **已安装**: 在 `requirements.txt` 中

## 🚀 快速启动

### 方式 1: 使用启动脚本 (推荐)

```bash
cd backend
./start_services.sh
```

这个脚本会自动:
1. 检查并启动 Redis
2. 启动 Celery worker
3. 启动 FastAPI 后端

### 方式 2: 手动启动

#### 步骤 1: 启动 Redis

```bash
# 使用 Docker 启动 Redis
docker run -d \
  --name code-reader-redis \
  -p 6379:6379 \
  --health-cmd "redis-cli ping" \
  --health-interval 5s \
  redis:7-alpine

# 验证 Redis
docker exec code-reader-redis redis-cli ping
# 应该返回: PONG
```

#### 步骤 2: 启动 Celery Worker

```bash
cd backend
source .venv/bin/activate  # 如果使用虚拟环境

# 前台运行 (用于调试)
celery -A celery_app worker --loglevel=info --concurrency=4 --queues=analysis

# 后台运行 (用于生产)
nohup celery -A celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --queues=analysis > celery_worker.log 2>&1 &
```

#### 步骤 3: 启动 FastAPI 后端

```bash
python run.py
```

## ⚙️ 配置

### 环境变量 (.env)

```bash
# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Celery 配置 (celery_app.py)

```python
celery_app.conf.update(
    task_time_limit=3600,        # 1小时硬超时
    task_soft_time_limit=3300,   # 55分钟软超时
    worker_prefetch_multiplier=1, # 每次只取1个任务
    worker_max_tasks_per_child=100, # 每个worker处理100个任务后重启
)
```

## 📊 监控

### API限制监控

当前配置基于以下API限制:
- **并发数**: 100
- **TPM** (Tokens Per Minute): 3,000,000
- **RPM** (Requests Per Minute): 500

**Celery Worker配置**:
- 并发数: 12 workers
- 预取倍数: 2 (每个worker预取2个任务)
- 最大同时处理: 24个任务

**监控要点**:
1. 确保RPM不超过500 (每个文件分析约1-3个请求)
2. 监控LLM API响应时间和错误率
3. 观察Celery worker的任务处理速度

### 查看 Celery 日志

```bash
# 实时查看日志
tail -f celery_worker.log

# 查看后端日志
tail -f backend.log

# 过滤错误信息
tail -f celery_worker.log | grep -E "ERROR|WARN|retry"
```

### 查看运行中的任务

```bash
# 查看正在执行的任务
celery -A celery_app inspect active

# 查看已注册的任务
celery -A celery_app inspect registered

# 查看任务队列
celery -A celery_app inspect reserved
```

### 查看 worker 状态

```bash
# 查看worker统计信息
celery -A celery_app inspect stats

# 查看worker配置
celery -A celery_app inspect conf

# 查看活跃的worker
celery -A celery_app inspect active_queues
```

### 监控Redis队列

```bash
# 进入Redis
docker exec -it mcp-redis redis-cli

# 查看队列长度
LLEN celery

# 查看队列内容
LRANGE celery 0 -1

# 查看所有键
KEYS *
```

### 性能监控

```bash
# 监控LLM API调用频率
tail -f backend.log | grep "HTTP Request: POST https://api.moonshot.cn"

# 监控任务完成情况
tail -f celery_worker.log | grep -E "succeeded|failed|retry"

# 统计每分钟的请求数(需要安装watch)
watch -n 60 'tail -100 backend.log | grep "HTTP Request: POST https://api.moonshot.cn" | wc -l'
```

### 使用Flower监控(推荐)

Flower是Celery的Web监控工具:

```bash
# 安装Flower
pip install flower

# 启动Flower
celery -A celery_app flower --port=5555

# 访问 http://localhost:5555 查看监控面板
```

Flower提供:
- 实时任务监控
- Worker状态
- 任务历史
- 任务统计图表
- 任务重试/撤销功能

## 🛑 停止服务

### 使用停止脚本

```bash
./stop_services.sh
```

### 手动停止

```bash
# 停止 Celery worker
pkill -f "celery.*worker"

# 停止后端
lsof -ti:8000 | xargs kill -9

# 停止 Redis (可选)
docker stop code-reader-redis
```

## 🔧 故障排查

### Redis 连接失败

```bash
# 检查 Redis 是否运行
docker ps | grep redis

# 检查端口是否被占用
lsof -i:6379

# 查看 Redis 日志
docker logs code-reader-redis
```

### Celery worker 无法启动

```bash
# 检查依赖是否安装
pip list | grep celery

# 检查 Redis 连接
python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(r.ping())"

# 查看详细错误
celery -A celery_app worker --loglevel=debug
```

### 任务执行失败

```bash
# 查看 Celery 日志
tail -100 celery_worker.log

# 检查任务状态
celery -A celery_app inspect registered
```

## 📝 任务列表

当前注册的 Celery 任务:

1. **`tasks.run_analysis_task`**: 运行完整的分析任务 (4个步骤)
2. **`tasks.analyze_single_file_task`**: 分析单个文件
3. **`tasks.batch_analyze_files_task`**: 批量分析多个文件

## 🎓 更多资源

- [Celery 官方文档](https://docs.celeryq.dev/)
- [Redis 官方文档](https://redis.io/docs/)
- [FastAPI 后台任务](https://fastapi.tiangolo.com/tutorial/background-tasks/)

