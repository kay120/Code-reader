# Celery Worker 监控配置

## 📊 监控功能

已在Web界面的服务状态中添加Celery Worker监控,实时显示worker运行状态。

## 🎯 监控内容

### 1. **Web界面监控**

在前端页面右上角的"服务状态"按钮中,可以看到:

- ✅ **Celery Worker状态**: 健康/不健康
- 📊 **Worker数量**: 当前运行的worker数量
- 🔄 **活跃任务数**: 正在执行的任务数量
- ⏱️ **响应时间**: API响应时间

**显示示例**:
```
Celery Worker
http://localhost:8000/celery/health
✓ 健康
响应时间: 45ms
1 workers, 0 活跃任务
```

### 2. **API端点**

#### GET `/celery/health`

返回Celery worker的详细状态信息。

**响应示例**:
```json
{
  "status": "healthy",
  "message": "1 个Celery worker运行正常",
  "timestamp": "2025-11-16T19:26:05.003153",
  "workers": [
    {
      "name": "celery@kaydeMacBook-Pro.local",
      "concurrency": 12,
      "active_tasks": 0,
      "total_tasks": {
        "tasks.run_analysis_task": 12
      }
    }
  ],
  "total_workers": 1,
  "total_active_tasks": 0
}
```

**状态码**:
- `200`: Worker运行正常
- `503`: Worker不可用或出错

## 🔧 配置说明

### API限制配置

当前配置基于以下API限制:
- **并发数**: 100
- **TPM** (Tokens Per Minute): 3,000,000
- **RPM** (Requests Per Minute): 500

### Celery Worker配置

- **并发数**: 12 workers
- **预取倍数**: 2 (每个worker预取2个任务)
- **最大同时处理**: 24个任务
- **任务超时**: 2小时硬限制, 1小时50分钟软限制

### 监控刷新频率

- **自动刷新**: 每60秒
- **手动刷新**: 点击"刷新"按钮
- **打开面板时**: 立即刷新一次

## 📈 监控指标说明

### 1. Worker数量 (total_workers)
- 正常值: 1 (单机部署)
- 异常值: 0 (worker未启动或崩溃)

### 2. 活跃任务数 (total_active_tasks)
- 正常值: 0-24 (根据并发配置)
- 警告值: >20 (接近满载)
- 异常值: >24 (超过配置的最大并发)

### 3. 响应时间
- 优秀: <100ms
- 良好: 100-500ms
- 警告: 500-2000ms
- 异常: >2000ms

## 🚨 告警规则

### Worker不可用
**症状**: API返回503状态码
**原因**: 
- Celery worker未启动
- Redis连接失败
- Worker进程崩溃

**解决方案**:
```bash
# 检查Celery worker进程
ps aux | grep "celery.*worker"

# 检查Redis
docker ps | grep redis

# 重启Celery worker
cd Code-reader/backend
./start_services.sh
```

### 任务堆积
**症状**: 活跃任务数持续接近或达到最大并发数
**原因**:
- 任务处理速度慢于提交速度
- LLM API响应慢
- 单个任务耗时过长

**解决方案**:
```bash
# 查看任务队列长度
docker exec -it mcp-redis redis-cli LLEN celery

# 查看正在执行的任务
celery -A celery_app inspect active

# 如果需要,增加worker并发数
celery -A celery_app worker --concurrency=16 --queues=analysis
```

## 📝 使用建议

1. **定期检查**: 每天查看一次服务状态,确保worker正常运行
2. **任务监控**: 创建分析任务后,观察活跃任务数变化
3. **性能优化**: 如果经常看到任务堆积,考虑增加worker并发数
4. **日志查看**: 出现异常时,查看 `celery_worker.log` 和 `backend.log`

## 🔗 相关文档

- [Celery配置文档](./CELERY_SETUP.md)
- [启动脚本](./start_services.sh)
- [停止脚本](./stop_services.sh)

