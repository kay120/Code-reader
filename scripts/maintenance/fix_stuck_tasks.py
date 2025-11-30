#!/usr/bin/env python3
"""修复卡住的任务"""

import sys
import os
from dotenv import load_dotenv
from datetime import datetime

backend_dir = os.path.join(os.path.dirname(__file__), 'Code-reader', 'backend')
sys.path.insert(0, backend_dir)
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

from database import SessionLocal
from models import AnalysisTask

db = SessionLocal()

# 修复 task 35 和 37
for task_id in [35, 37]:
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if task:
        print(f'Task {task_id}:')
        print(f'  当前状态: {task.status}')
        print(f'  Total Files: {task.total_files}')
        print(f'  Successful: {task.successful_files}')
        
        # 更新状态为 completed
        task.status = 'completed'
        task.end_time = datetime.now()
        task.current_file = None
        
        print(f'  ✅ 已更新为: completed')
        print()

db.commit()
db.close()

print('✅ 任务状态已更新，现在需要重启 Celery Worker')

