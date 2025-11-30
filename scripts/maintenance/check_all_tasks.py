#!/usr/bin/env python3
"""检查所有任务的文件统计"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
backend_dir = os.path.join(os.path.dirname(__file__), 'Code-reader', 'backend')
sys.path.insert(0, backend_dir)
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

from database import SessionLocal
from models import FileAnalysis, AnalysisTask
from sqlalchemy import func

db = SessionLocal()

# 统计所有任务的文件数
task_stats = db.query(
    FileAnalysis.task_id,
    FileAnalysis.status,
    func.count(FileAnalysis.id).label('count')
).group_by(
    FileAnalysis.task_id,
    FileAnalysis.status
).all()

print('📊 所有任务的文件统计:')
print('=' * 70)

# 按任务ID分组
from collections import defaultdict
tasks = defaultdict(lambda: defaultdict(int))
for task_id, status, count in task_stats:
    tasks[task_id][status] = count

for task_id in sorted(tasks.keys()):
    # 获取任务信息
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if task:
        print(f'\nTask {task_id} ({task.status}):')
        total = 0
        for status, count in tasks[task_id].items():
            print(f'  {status}: {count} 个文件')
            total += count
        print(f'  总计: {total} 个文件')

# 统计所有 pending 状态的文件
total_pending = db.query(func.count(FileAnalysis.id)).filter(
    FileAnalysis.status == 'pending'
).scalar()

print('\n' + '=' * 70)
print(f'📝 所有任务的 pending 文件总数: {total_pending}')

db.close()

