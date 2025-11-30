#!/usr/bin/env python3
"""手动触发 task 41"""

import sys
import os
from dotenv import load_dotenv

backend_dir = os.path.join(os.path.dirname(__file__), 'Code-reader', 'backend')
sys.path.insert(0, backend_dir)
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

from database import SessionLocal
from models import AnalysisTask, Repository
from tasks import run_analysis_task

db = SessionLocal()

# 查找 task 41
task = db.query(AnalysisTask).filter(AnalysisTask.id == 41).first()
if task:
    print(f'Task 41:')
    print(f'  Status: {task.status}')
    print(f'  Repository ID: {task.repository_id}')
    
    # 查找仓库
    repo = db.query(Repository).filter(Repository.id == task.repository_id).first()
    if repo:
        print(f'  Repository: {repo.name}')
        print(f'  Local Path: {repo.local_path}')
        
        # 触发 Celery 任务
        print(f'\n🚀 触发 Celery 任务...')
        result = run_analysis_task.apply_async(
            kwargs={
                'task_id': task.id,
                'external_file_path': repo.local_path
            },
            queue='analysis'
        )
        
        print(f'✅ Celery 任务已发送到队列')
        print(f'   Task ID: {result.id}')
        print(f'   Status: {result.status}')
else:
    print('Task 41 not found')

db.close()

