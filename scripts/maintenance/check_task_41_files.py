#!/usr/bin/env python3
"""检查 task 41 的文件数量"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# 加载环境变量
backend_dir = Path(__file__).parent / 'Code-reader' / 'backend'
env_path = backend_dir / '.env'
load_dotenv(env_path)

# 添加 backend 到路径
sys.path.insert(0, str(backend_dir))

from models import FileAnalysis

# 创建数据库连接
db_url = f"{os.getenv('DB_DIALECT')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?{os.getenv('DB_PARAMS')}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
db = Session()

# 查询 task 41 的文件
total_files = db.query(FileAnalysis).filter(FileAnalysis.task_id == 41).count()
unique_files = db.query(func.count(func.distinct(FileAnalysis.file_path))).filter(FileAnalysis.task_id == 41).scalar()

print(f'Task 41 文件统计:')
print(f'  总记录数: {total_files}')
print(f'  唯一文件数: {unique_files}')

# 检查是否有重复
if total_files > unique_files:
    print(f'\n⚠️  发现重复记录: {total_files - unique_files} 条')
    
    # 查找重复的文件
    duplicates = db.query(
        FileAnalysis.file_path,
        func.count(FileAnalysis.id).label('count')
    ).filter(
        FileAnalysis.task_id == 41
    ).group_by(
        FileAnalysis.file_path
    ).having(
        func.count(FileAnalysis.id) > 1
    ).order_by(
        func.count(FileAnalysis.id).desc()
    ).limit(10).all()
    
    print('\n重复最多的文件（前10）:')
    for file_path, count in duplicates:
        print(f'  {count}x - {file_path}')

db.close()

