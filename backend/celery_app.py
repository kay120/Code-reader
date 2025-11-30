"""
Celery应用配置
用于处理后台异步任务,避免阻塞API请求
"""
import os
import sys
from pathlib import Path
from celery import Celery
from celery.signals import worker_process_init
from dotenv import load_dotenv

# 确保backend目录和Code-reader目录在Python路径中
backend_dir = Path(__file__).parent.absolute()
code_reader_dir = backend_dir.parent  # Code-reader目录

# 加载 .env 文件（指定完整路径）
env_path = backend_dir / '.env'
load_dotenv(env_path)

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(code_reader_dir) not in sys.path:
    sys.path.insert(0, str(code_reader_dir))

# 在worker子进程初始化时也添加路径和加载环境变量
@worker_process_init.connect
def init_worker_process(**kwargs):
    """在每个worker子进程初始化时执行"""
    backend_dir = Path(__file__).parent.absolute()
    code_reader_dir = backend_dir.parent

    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    if str(code_reader_dir) not in sys.path:
        sys.path.insert(0, str(code_reader_dir))

    # 重新加载环境变量（子进程需要重新加载）
    env_path = backend_dir / '.env'
    load_dotenv(env_path, override=True)

# 延迟导入config以确保路径已设置
from config import settings

# 创建Celery应用
celery_app = Celery(
    "code_reader",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

# Celery配置
# API限制: 并发100, TPM 3,000,000, RPM 500
# 用户配置: 并发10 (控制并发数避免过载)
# 建议配置:
# - Celery workers: 10个并发
# - 每个文件分析约需要1-3个LLM请求
# - 控制并发避免超过RPM限制
celery_app.conf.update(
    # 任务序列化格式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务结果过期时间(秒)
    result_expires=3600,

    # Worker配置 - 可通过环境变量 CELERY_WORKER_CONCURRENCY 调整并发数
    worker_prefetch_multiplier=2,  # 每个worker预取2个任务,提高吞吐量
    worker_max_tasks_per_child=200,  # 每个worker处理200个任务后重启,防止内存泄漏
    worker_concurrency=int(os.getenv("CELERY_WORKER_CONCURRENCY", "10")),  # 默认10,可通过环境变量覆盖

    # 任务路由 - 注释掉，使用默认队列 celery
    # task_routes={
    #     "tasks.run_analysis_task": {"queue": "analysis"},
    #     "tasks.analyze_single_file_task": {"queue": "analysis"},
    #     "tasks.batch_analyze_files_task": {"queue": "analysis"},
    # },

    # 任务时间限制
    task_time_limit=7200,  # 2小时硬限制(完整分析任务可能需要更长时间)
    task_soft_time_limit=6600,  # 1小时50分钟软限制

    # 任务重试配置
    task_acks_late=True,  # 任务完成后才确认,失败时可重新分配
    task_reject_on_worker_lost=True,  # worker丢失时拒绝任务,允许重新分配
)

# 手动导入任务模块以注册任务
import tasks  # noqa: F401

if __name__ == "__main__":
    celery_app.start()

