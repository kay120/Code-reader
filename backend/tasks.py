"""
Celery异步任务
用于处理耗时的后台任务,避免阻塞API请求
"""
import asyncio
import logging
import sys
from pathlib import Path

# 确保backend目录在Python路径中(Celery子进程需要)
backend_dir = Path(__file__).parent.absolute()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.run_analysis_task", bind=True)
def run_analysis_task(self, task_id: int, external_file_path: str):
    """
    Celery异步任务: 运行完整的分析任务

    这是主要的后台任务,包含所有4个步骤:
    - 步骤0: 扫描代码文件
    - 步骤1: 创建知识库
    - 步骤2: 分析数据模型
    - 步骤3: 生成文档结构

    Args:
        task_id: 分析任务ID
        external_file_path: 外部文件路径

    Returns:
        dict: 任务执行结果
    """
    try:
        logger.info(f"🚀 Celery任务开始: 运行分析任务 {task_id}")

        # 导入run_task函数(延迟导入避免循环依赖)
        import sys
        from pathlib import Path
        # 确保backend目录在Python路径中
        backend_dir = Path(__file__).parent.absolute()
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))

        from service.task_service import run_task

        # 在新的事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                run_task(task_id=task_id, external_file_path=external_file_path)
            )

            # 检查执行结果
            if result.get("status") == "success":
                logger.info(f"✅ Celery任务成功: 分析任务 {task_id} 完成")
                return {
                    "status": "success",
                    "task_id": task_id,
                    "message": result.get("message", "任务执行完成"),
                }
            else:
                logger.error(f"❌ Celery任务失败: 分析任务 {task_id} 失败 - {result}")
                return {
                    "status": "failed",
                    "task_id": task_id,
                    "error": result.get("message", "未知错误"),
                }
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ Celery任务异常: 分析任务 {task_id} 出错 - {str(e)}", exc_info=True)
        # 重试任务(最多2次,每次延迟120秒)
        raise self.retry(exc=e, countdown=120, max_retries=2)


@celery_app.task(name="tasks.analyze_single_file_task", bind=True)
def analyze_single_file_task(self, task_id: int, file_id: int, vectorstore_index: str):
    """
    Celery异步任务: 分析单个文件的数据模型

    Args:
        task_id: 分析任务ID
        file_id: 文件ID
        vectorstore_index: 向量存储索引名称

    Returns:
        dict: 分析结果
    """
    try:
        logger.info(f"🚀 Celery任务开始: 分析文件 {file_id} (任务ID: {task_id})")

        # 更新任务的current_file字段
        from database import SessionLocal
        from models import AnalysisTask, FileAnalysis

        db = SessionLocal()
        try:
            # 获取文件路径
            file_analysis = db.query(FileAnalysis).filter(FileAnalysis.id == file_id).first()
            if file_analysis:
                # 更新任务的当前处理文件
                task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                if task:
                    task.current_file = file_analysis.file_path
                    db.commit()
                    logger.info(f"📝 更新任务 {task_id} 当前处理文件: {file_analysis.file_path}")
        except Exception as e:
            logger.warning(f"更新current_file失败: {str(e)}")
            db.rollback()
        finally:
            db.close()

        # 导入flow函数(延迟导入避免循环依赖)
        from src.flows.web_flow import analyze_single_file_data_model

        # 在新的事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                analyze_single_file_data_model(
                    task_id=task_id,
                    file_id=file_id,
                    vectorstore_index=vectorstore_index
                )
            )

            # 检查flow执行结果
            if result.get("status") == "completed":
                analysis_items_count = result.get("analysis_items_count", 0)
                logger.info(f"✅ Celery任务成功: 文件 {file_id} 分析完成,创建了 {analysis_items_count} 个分析项")

                # ========== 检查是否所有文件都已分析完成 ==========
                db = SessionLocal()
                try:
                    # 查询任务下的所有文件分析记录
                    all_files = db.query(FileAnalysis).filter(FileAnalysis.task_id == task_id).all()
                    total_files = len(all_files)
                    completed_files = sum(1 for f in all_files if f.status == 'success')
                    failed_files = sum(1 for f in all_files if f.status == 'failed')
                    pending_files = sum(1 for f in all_files if f.status == 'pending')

                    logger.info(f"📊 任务 {task_id} 进度: {completed_files}/{total_files} 完成, {failed_files} 失败, {pending_files} 待处理")

                    # 如果所有文件都已处理完成（成功或失败），触发步骤 3
                    if pending_files == 0:
                        logger.info(f"🎉 任务 {task_id} 所有文件分析完成！准备触发步骤 3（生成文档）")

                        # 获取任务信息
                        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                        if task:
                            # 获取仓库信息
                            from models import Repository
                            repository = db.query(Repository).filter(Repository.id == task.repository_id).first()
                            if repository:
                                external_file_path = repository.local_path

                                # 异步触发步骤 3
                                logger.info(f"🚀 触发步骤 3: 生成文档结构")
                                from tasks import generate_document_task
                                generate_document_task.delay(task_id, external_file_path)
                                logger.info(f"✅ 步骤 3 已提交到后台队列")
                except Exception as e:
                    logger.error(f"检查任务完成状态失败: {str(e)}")
                finally:
                    db.close()

                return {
                    "status": "success",
                    "file_id": file_id,
                    "analysis_items_count": analysis_items_count,
                }
            else:
                logger.error(f"❌ Celery任务失败: 文件 {file_id} 分析失败 - {result}")
                return {
                    "status": "failed",
                    "file_id": file_id,
                    "error": str(result),
                }
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ Celery任务异常: 文件 {file_id} 分析出错 - {str(e)}", exc_info=True)
        # 重试任务(最多3次,每次延迟60秒)
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(name="tasks.generate_document_task", bind=True)
def generate_document_task(self, task_id: int, external_file_path: str):
    """
    Celery异步任务: 生成文档结构（步骤 3）

    Args:
        task_id: 分析任务ID
        external_file_path: 外部文件路径

    Returns:
        dict: 任务执行结果
    """
    try:
        logger.info(f"🚀 Celery任务开始: 生成文档结构 (任务ID: {task_id})")

        # 导入函数
        from service.task_service import execute_step_3_generate_document_structure
        from database import SessionLocal
        from models import AnalysisTask, Repository

        # 获取任务和仓库信息
        db = SessionLocal()
        try:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not task:
                logger.error(f"未找到任务 {task_id}")
                return {"status": "failed", "error": "任务不存在"}

            repository = db.query(Repository).filter(Repository.id == task.repository_id).first()
            if not repository:
                logger.error(f"未找到仓库 {task.repository_id}")
                return {"status": "failed", "error": "仓库不存在"}

            repo_info = {
                "id": repository.id,
                "name": repository.name,
                "local_path": repository.local_path,
            }
        finally:
            db.close()

        # 在新的事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                execute_step_3_generate_document_structure(task_id, external_file_path, repo_info)
            )

            # 检查执行结果
            if result.get("success"):
                logger.info(f"✅ Celery任务成功: 文档生成完成 (任务ID: {task_id})")

                # 更新任务状态为完成
                db = SessionLocal()
                try:
                    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                    if task:
                        task.status = "completed"
                        from datetime import datetime
                        task.end_time = datetime.now()
                        task.progress_percentage = 100
                        task.current_file = None
                        db.commit()
                        logger.info(f"✅ 任务 {task_id} 已标记为完成")
                finally:
                    db.close()

                return {
                    "status": "success",
                    "task_id": task_id,
                    "message": "文档生成完成",
                }
            else:
                logger.warning(f"⚠️ Celery任务失败: 文档生成失败 (任务ID: {task_id}) - {result.get('message', '未知错误')}")
                # 文档生成失败不影响整体任务，仍然标记为完成
                db = SessionLocal()
                try:
                    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                    if task:
                        task.status = "completed"
                        from datetime import datetime
                        task.end_time = datetime.now()
                        task.progress_percentage = 100
                        task.current_file = None
                        db.commit()
                        logger.info(f"✅ 任务 {task_id} 已标记为完成（文档生成失败但不影响整体）")
                finally:
                    db.close()

                return {
                    "status": "success",
                    "task_id": task_id,
                    "message": "文件分析完成，但文档生成失败",
                }
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"❌ Celery任务异常: 文档生成出错 (任务ID: {task_id}) - {str(e)}", exc_info=True)
        # 不重试，直接标记任务为完成
        db = SessionLocal()
        try:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if task:
                task.status = "completed"
                from datetime import datetime
                task.end_time = datetime.now()
                task.progress_percentage = 100
                task.current_file = None
                db.commit()
                logger.info(f"✅ 任务 {task_id} 已标记为完成（文档生成异常但不影响整体）")
        finally:
            db.close()

        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
        }


@celery_app.task(name="tasks.batch_analyze_files_task")
def batch_analyze_files_task(task_id: int, file_ids: list, vectorstore_index: str):
    """
    Celery异步任务: 批量分析多个文件

    Args:
        task_id: 分析任务ID
        file_ids: 文件ID列表
        vectorstore_index: 向量存储索引名称
        
    Returns:
        dict: 批量分析结果
    """
    try:
        logger.info(f"🚀 Celery批量任务开始: 分析 {len(file_ids)} 个文件 (任务ID: {task_id})")
        
        results = []
        for file_id in file_ids:
            # 为每个文件创建一个子任务
            result = analyze_single_file_task.delay(task_id, file_id, vectorstore_index)
            results.append({
                "file_id": file_id,
                "celery_task_id": result.id,
            })
        
        logger.info(f"✅ Celery批量任务已分发: {len(results)} 个子任务")
        return {
            "status": "dispatched",
            "task_id": task_id,
            "total_files": len(file_ids),
            "subtasks": results,
        }
        
    except Exception as e:
        logger.error(f"❌ Celery批量任务异常: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
        }

