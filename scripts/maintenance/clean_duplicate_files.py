#!/usr/bin/env python3
"""
清理 task_id=37 的重复文件记录
只保留每个文件路径的最新记录（ID最大的）
"""

import sys
import os
from dotenv import load_dotenv

# 添加 backend 目录到路径
backend_dir = os.path.join(os.path.dirname(__file__), 'Code-reader', 'backend')
sys.path.insert(0, backend_dir)

# 加载 backend 目录的 .env 文件
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)
print(f"📁 加载环境变量: {env_path}")
print(f"📊 数据库: {os.getenv('DB_NAME')}")
print()

from database import SessionLocal
from models import FileAnalysis
from sqlalchemy import func, and_

def clean_duplicate_files(task_id: int, dry_run: bool = True):
    """
    清理指定任务的重复文件记录
    
    Args:
        task_id: 任务ID
        dry_run: 是否只是预览，不实际删除
    """
    db = SessionLocal()
    
    try:
        # 1. 统计当前状态
        total_records = db.query(FileAnalysis).filter(FileAnalysis.task_id == task_id).count()
        unique_files = db.query(func.count(func.distinct(FileAnalysis.file_path))).filter(
            FileAnalysis.task_id == task_id
        ).scalar()
        
        print(f"📊 任务 {task_id} 当前状态:")
        print(f"   总记录数: {total_records}")
        print(f"   唯一文件数: {unique_files}")
        print(f"   重复记录数: {total_records - unique_files}")
        print()
        
        if total_records == unique_files:
            print("✅ 没有重复记录，无需清理")
            return
        
        # 2. 找出每个文件路径的最大ID（最新记录）
        subquery = db.query(
            FileAnalysis.file_path,
            func.max(FileAnalysis.id).label('max_id')
        ).filter(
            FileAnalysis.task_id == task_id
        ).group_by(
            FileAnalysis.file_path
        ).subquery()
        
        # 3. 查询所有要保留的记录ID
        keep_ids = db.query(subquery.c.max_id).all()
        keep_ids = [id[0] for id in keep_ids]
        
        print(f"🔍 将保留 {len(keep_ids)} 条最新记录")
        
        # 4. 查询要删除的记录
        delete_records = db.query(FileAnalysis).filter(
            and_(
                FileAnalysis.task_id == task_id,
                FileAnalysis.id.notin_(keep_ids)
            )
        ).all()
        
        print(f"🗑️  将删除 {len(delete_records)} 条重复记录")
        print()
        
        if dry_run:
            print("⚠️  这是预览模式，不会实际删除数据")
            print("   如果确认要删除，请运行: python clean_duplicate_files.py --execute")
            print()
            
            # 显示一些示例
            print("📝 重复记录示例（前5个文件）:")
            file_counts = {}
            for record in delete_records[:20]:
                if record.file_path not in file_counts:
                    file_counts[record.file_path] = 0
                file_counts[record.file_path] += 1
            
            for file_path, count in list(file_counts.items())[:5]:
                print(f"   {file_path}: {count} 条重复")
        else:
            print("⚠️  开始删除重复记录...")
            
            # 批量删除
            deleted_count = db.query(FileAnalysis).filter(
                and_(
                    FileAnalysis.task_id == task_id,
                    FileAnalysis.id.notin_(keep_ids)
                )
            ).delete(synchronize_session=False)
            
            db.commit()
            
            print(f"✅ 成功删除 {deleted_count} 条重复记录")
            
            # 验证结果
            final_count = db.query(FileAnalysis).filter(FileAnalysis.task_id == task_id).count()
            print(f"✅ 清理后剩余 {final_count} 条记录")
            
    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # 支持命令行参数指定 task_id
    task_id = 37
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        task_id = int(sys.argv[1])

    # 检查是否有 --execute 参数
    dry_run = "--execute" not in sys.argv

    print("=" * 60)
    print("清理重复文件记录工具")
    print("=" * 60)
    print()

    clean_duplicate_files(task_id, dry_run=dry_run)

    print()
    print("=" * 60)

