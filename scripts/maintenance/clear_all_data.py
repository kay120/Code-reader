#!/usr/bin/env python3
"""清空所有数据库数据和本地文件"""

import sys
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 加载环境变量
backend_dir = Path(__file__).parent / 'Code-reader' / 'backend'
env_path = backend_dir / '.env'
load_dotenv(env_path)

# 添加 backend 到路径
sys.path.insert(0, str(backend_dir))

from models import Repository, AnalysisTask, FileAnalysis, TaskReadme

# 创建数据库连接
db_url = f"{os.getenv('DB_DIALECT')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?{os.getenv('DB_PARAMS')}"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
db = Session()

print('🗑️  开始清空所有数据...\n')

# 1. 统计当前数据
repo_count = db.query(Repository).count()
task_count = db.query(AnalysisTask).count()
file_count = db.query(FileAnalysis).count()
readme_count = db.query(TaskReadme).count()

print('📊 当前数据统计:')
print(f'  Repository: {repo_count}')
print(f'  AnalysisTask: {task_count}')
print(f'  FileAnalysis: {file_count}')
print(f'  TaskReadme: {readme_count}')
print()

# 2. 删除数据库记录（按照外键依赖顺序）
print('🗄️  清空数据库表...')

# 先删除子表
db.query(TaskReadme).delete()
print('  ✅ TaskReadme 已清空')

db.query(FileAnalysis).delete()
print('  ✅ FileAnalysis 已清空')

db.query(AnalysisTask).delete()
print('  ✅ AnalysisTask 已清空')

db.query(Repository).delete()
print('  ✅ Repository 已清空')

# 重置自增ID
try:
    db.execute(text('ALTER TABLE repository AUTO_INCREMENT = 1'))
    db.execute(text('ALTER TABLE analysis_task AUTO_INCREMENT = 1'))
    db.execute(text('ALTER TABLE file_analysis AUTO_INCREMENT = 1'))
    db.execute(text('ALTER TABLE task_readme AUTO_INCREMENT = 1'))
    print('  ✅ 自增ID已重置')
except Exception as e:
    print(f'  ⚠️  重置自增ID失败: {e}')

db.commit()
print()

# 3. 清空本地文件
repos_dir = backend_dir / 'data' / 'repos'
results_dir = backend_dir / 'data' / 'results'
vectorstores_dir = backend_dir / 'data' / 'vectorstores'

print('📁 清空本地文件...')

if repos_dir.exists():
    for item in repos_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
            print(f'  ✅ 删除仓库目录: {item.name}')
    print(f'  ✅ {repos_dir} 已清空')
else:
    print(f'  ℹ️  {repos_dir} 不存在')

if results_dir.exists():
    for item in results_dir.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    print(f'  ✅ {results_dir} 已清空')
else:
    print(f'  ℹ️  {results_dir} 不存在')

if vectorstores_dir.exists():
    for item in vectorstores_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
    print(f'  ✅ {vectorstores_dir} 已清空')
else:
    print(f'  ℹ️  {vectorstores_dir} 不存在')

print()
print('✅ 所有数据已清空！')
print('现在可以重新上传仓库了。')

db.close()

