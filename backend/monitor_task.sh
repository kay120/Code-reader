#!/bin/bash
# 监控任务执行状态

cd /Users/kay/code/work/codereader_workspace/Code-reader/backend
source .venv/bin/activate

echo "=== 开始监控任务 11 ==="
echo ""

for i in {1..20}; do
    python3 << 'EOF'
from sqlalchemy import create_engine
from urllib.parse import quote_plus

encoded_password = quote_plus('123456')
database_url = f'mysql+pymysql://root:{encoded_password}@localhost:3306/code_analysis?charset=utf8mb4'
engine = create_engine(database_url)

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
db = Session()

from models import AnalysisTask, FileAnalysis

task = db.query(AnalysisTask).filter(AnalysisTask.id == 11).first()
if task:
    file_count = db.query(FileAnalysis).filter(FileAnalysis.task_id == 11).count()
    print(f'[{task.status}] 成功: {task.successful_files}/{task.total_files}, FileAnalysis: {file_count}')
    
    if task.status in ['completed', 'failed']:
        print(f'\n任务已结束: {task.status}')
        exit(0)

db.close()
EOF
    
    sleep 10
done

echo ""
echo "=== 监控结束 ==="

