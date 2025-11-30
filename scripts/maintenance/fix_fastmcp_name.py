#!/usr/bin/env python3
"""修复 fastmcp 仓库的名称"""

import sys
import os
from dotenv import load_dotenv

backend_dir = os.path.join(os.path.dirname(__file__), 'Code-reader', 'backend')
sys.path.insert(0, backend_dir)
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

from database import SessionLocal
from models import Repository, TaskReadme

db = SessionLocal()

# 更新 repository 33 的名称
repo = db.query(Repository).filter(Repository.id == 33).first()
if repo:
    print(f'Repository 33:')
    print(f'  当前 Name: {repo.name}')
    print(f'  当前 Full Name: {repo.full_name}')
    
    # 更新为正确的名称
    repo.full_name = 'jlowin/fastmcp'
    
    print(f'  ✅ 已更新 Full Name: {repo.full_name}')

# 更新 task 35 的 README 标题
readme = db.query(TaskReadme).filter(TaskReadme.task_id == 35).first()
if readme:
    print(f'\nTask 35 README:')
    print(f'  当前标题: {readme.content[:100]}')
    
    # 替换标题
    old_title = '# 0ddc6cd274dbf800e7642aa54efaa387 项目技术文档'
    new_title = '# FastMCP 项目技术文档'
    
    if old_title in readme.content:
        readme.content = readme.content.replace(old_title, new_title, 1)
        print(f'  ✅ 已更新标题为: {new_title}')
    else:
        print(f'  ⚠️  未找到旧标题')

db.commit()
db.close()

print('\n✅ 更新完成！')

