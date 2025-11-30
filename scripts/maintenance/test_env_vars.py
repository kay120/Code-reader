#!/usr/bin/env python3
"""测试环境变量是否正确加载"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量（和 celery_app.py 一样的方式）
backend_dir = Path(__file__).parent / 'Code-reader' / 'backend'
env_path = backend_dir / '.env'
load_dotenv(env_path)

print(f'📁 .env 文件路径: {env_path}')
print(f'📁 .env 文件存在: {env_path.exists()}')
print()

# 检查关键环境变量
env_vars = [
    'OPENAI_API_KEY',
    'OPENAI_BASE_URL',
    'OPENAI_MODEL',
    'CELERY_WORKER_CONCURRENCY',
    'DB_NAME',
]

print('🔍 环境变量检查:')
print('=' * 70)
for var in env_vars:
    value = os.getenv(var)
    if value:
        # 隐藏敏感信息
        if 'KEY' in var or 'PASSWORD' in var:
            display_value = value[:10] + '...' if len(value) > 10 else value
        else:
            display_value = value
        print(f'✅ {var}: {display_value}')
    else:
        print(f'❌ {var}: 未设置')

