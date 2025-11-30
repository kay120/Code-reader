#!/usr/bin/env python3
"""检查任务文件状态"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
backend_dir = os.path.join(os.path.dirname(__file__), 'Code-reader', 'backend')
sys.path.insert(0, backend_dir)
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

from database import SessionLocal
from models import FileAnalysis
from sqlalchemy import func

db = SessionLocal()

task_id = 37

# 统计各状态的文件数
status_counts = db.query(
    FileAnalysis.status,
    func.count(FileAnalysis.id).label('count')
).filter(
    FileAnalysis.task_id == task_id
).group_by(
    FileAnalysis.status
).all()

print(f'📊 Task {task_id} 文件状态统计:')
print('=' * 50)
total = 0
for status, count in status_counts:
    print(f'  {status}: {count} 个文件')
    total += count
print('=' * 50)
print(f'  总计: {total} 个文件')

# 检查是否有重复的文件路径
print('\n🔍 检查重复文件:')
duplicates = db.query(
    FileAnalysis.file_path,
    func.count(FileAnalysis.id).label('count')
).filter(
    FileAnalysis.task_id == task_id
).group_by(
    FileAnalysis.file_path
).having(
    func.count(FileAnalysis.id) > 1
).all()

if duplicates:
    print(f'  ⚠️  发现 {len(duplicates)} 个重复文件:')
    for file_path, count in duplicates[:5]:
        print(f'    {file_path}: {count} 次')
else:
    print('  ✅ 没有重复文件')

db.close()

