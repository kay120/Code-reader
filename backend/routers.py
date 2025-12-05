"""
API路由定义
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from tasks import analyze_single_file_task
from services import (
    FileAnalysisService,
    AnalysisItemService,
    RepositoryService,
    AnalysisTaskService,
    UploadService,
    TaskReadmeService,
)
from models import AnalysisTask, Repository, FileAnalysis
from typing import Optional, List
from pydantic import BaseModel, Field
import logging
import os
import zipfile
import tempfile
import shutil
import requests
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置logger
logger = logging.getLogger(__name__)


# Pydantic模型定义
class RepositoryCreate(BaseModel):
    """创建仓库的请求模型"""

    user_id: Optional[int] = Field(default=1, description="用户ID，默认为1")
    name: str = Field(..., min_length=1, max_length=255, description="仓库名称")
    full_name: Optional[str] = Field(None, max_length=255, description="完整仓库名")
    local_path: str = Field(..., min_length=1, max_length=1024, description="本地仓库路径")
    status: Optional[int] = Field(default=1, description="状态：1=存在，0=已删除")


class RepositoryUpdate(BaseModel):
    """更新仓库的请求模型"""

    user_id: Optional[int] = Field(None, description="用户ID")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="仓库名称")
    full_name: Optional[str] = Field(None, max_length=255, description="完整仓库名")
    local_path: Optional[str] = Field(None, min_length=1, max_length=1024, description="本地仓库路径")
    status: Optional[int] = Field(None, description="状态：1=存在，0=已删除")


class AnalysisTaskCreate(BaseModel):
    """创建分析任务的请求模型"""

    repository_id: int = Field(..., description="仓库ID")
    total_files: Optional[int] = Field(default=0, description="总文件数")
    successful_files: Optional[int] = Field(default=0, description="成功分析文件数")
    failed_files: Optional[int] = Field(default=0, description="失败文件数")
    code_lines: Optional[int] = Field(default=0, description="代码行数")
    module_count: Optional[int] = Field(default=0, description="模块数量")
    status: Optional[str] = Field(default="pending", description="任务状态：pending/running/completed/failed")
    start_time: Optional[str] = Field(None, description="开始时间（ISO格式）")
    end_time: Optional[str] = Field(None, description="结束时间（ISO格式）")
    task_index: Optional[str] = Field(None, description="任务索引")


class AnalysisTaskUpdate(BaseModel):
    """更新分析任务的请求模型"""

    repository_id: Optional[int] = Field(None, description="仓库ID")
    total_files: Optional[int] = Field(None, description="总文件数")
    successful_files: Optional[int] = Field(None, description="成功分析文件数")
    failed_files: Optional[int] = Field(None, description="失败文件数")
    code_lines: Optional[int] = Field(None, description="代码行数")
    module_count: Optional[int] = Field(None, description="模块数量")
    status: Optional[str] = Field(None, description="任务状态：pending/running/completed/failed")
    start_time: Optional[str] = Field(None, description="开始时间（ISO格式）")
    end_time: Optional[str] = Field(None, description="结束时间（ISO格式）")
    task_index: Optional[str] = Field(None, description="任务索引")
    current_file: Optional[str] = Field(None, description="当前处理的文件")


class FileAnalysisCreate(BaseModel):
    """创建文件分析记录的请求模型"""

    task_id: int = Field(..., description="分析任务ID")
    file_path: str = Field(..., min_length=1, max_length=1024, description="文件路径")
    language: Optional[str] = Field(None, max_length=64, description="编程语言")
    analysis_version: Optional[str] = Field(default="1.0", max_length=32, description="分析版本")
    status: Optional[str] = Field(default="pending", description="分析状态：pending/success/failed")
    code_lines: Optional[int] = Field(default=0, description="代码行数")
    code_content: Optional[str] = Field(None, description="代码内容")
    file_analysis: Optional[str] = Field(None, description="文件分析结果")
    dependencies: Optional[str] = Field(None, description="依赖模块列表")
    error_message: Optional[str] = Field(None, description="错误信息")


class FileAnalysisUpdate(BaseModel):
    """更新文件分析记录的请求模型"""

    task_id: Optional[int] = Field(None, description="分析任务ID")
    file_path: Optional[str] = Field(None, min_length=1, max_length=1024, description="文件路径")
    language: Optional[str] = Field(None, max_length=64, description="编程语言")
    analysis_version: Optional[str] = Field(None, max_length=32, description="分析版本")
    status: Optional[str] = Field(None, description="分析状态：pending/success/failed")
    code_lines: Optional[int] = Field(None, description="代码行数")
    code_content: Optional[str] = Field(None, description="代码内容")
    file_analysis: Optional[str] = Field(None, description="文件分析结果")
    dependencies: Optional[str] = Field(None, description="依赖模块列表")
    error_message: Optional[str] = Field(None, description="错误信息")


class AnalysisItemCreate(BaseModel):
    """创建分析项记录的请求模型"""

    file_analysis_id: int = Field(..., description="文件分析ID")
    title: str = Field(..., min_length=1, max_length=512, description="标题")
    description: Optional[str] = Field(None, description="描述")
    target_type: Optional[str] = Field(None, max_length=32, description="目标类型：file/class/function")
    target_name: Optional[str] = Field(None, max_length=255, description="目标名称（类名/函数名）")
    source: Optional[str] = Field(None, max_length=1024, description="源码位置")
    language: Optional[str] = Field(None, max_length=64, description="编程语言")
    code: Optional[str] = Field(None, description="代码片段")
    start_line: Optional[int] = Field(None, description="起始行号")
    end_line: Optional[int] = Field(None, description="结束行号")


class AnalysisItemUpdate(BaseModel):
    """更新分析项记录的请求模型"""

    file_analysis_id: Optional[int] = Field(None, description="文件分析ID")
    title: Optional[str] = Field(None, min_length=1, max_length=512, description="标题")
    description: Optional[str] = Field(None, description="描述")
    target_type: Optional[str] = Field(None, max_length=32, description="目标类型：file/class/function")
    target_name: Optional[str] = Field(None, max_length=255, description="目标名称（类名/函数名）")
    source: Optional[str] = Field(None, max_length=1024, description="源码位置")
    language: Optional[str] = Field(None, max_length=64, description="编程语言")
    code: Optional[str] = Field(None, description="代码片段")
    start_line: Optional[int] = Field(None, description="起始行号")
    end_line: Optional[int] = Field(None, description="结束行号")


class TaskReadmeCreate(BaseModel):
    """创建任务README的请求模型"""

    task_id: int = Field(..., description="任务ID")
    content: str = Field(..., min_length=1, description="readme的完整内容")


class TaskReadmeUpdate(BaseModel):
    """更新任务README的请求模型"""

    task_id: Optional[int] = Field(None, description="任务ID")
    content: Optional[str] = Field(None, min_length=1, description="readme的完整内容")


class PasswordVerifyRequest(BaseModel):
    """密码验证请求模型"""

    password: str = Field(..., min_length=1, description="密码")


# 创建路由器
repository_router = APIRouter(prefix="/api/repository", tags=["仓库管理"])
analysis_router = APIRouter(prefix="/api/analysis", tags=["分析管理"])
auth_router = APIRouter(prefix="/api/auth", tags=["认证管理"])


@auth_router.post("/verify-password")
async def verify_password(request: PasswordVerifyRequest):
    """
    验证密码
    """
    try:
        # 从环境变量获取设置的密码
        correct_password = os.getenv("PASSWORD", "123456")

        if request.password == correct_password:
            return JSONResponse(status_code=200, content={"success": True, "message": "密码验证成功"})
        else:
            return JSONResponse(status_code=200, content={"success": False, "message": "密码错误"})
    except Exception as e:
        logger.error(f"密码验证时发生错误: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "message": "服务器内部错误"})


@repository_router.get("/repositories/{repository_id}")
async def get_repository_by_id(
    repository_id: int,
    db: Session = Depends(get_db),
    include_tasks: bool = Query(False, description="是否包含分析任务信息"),
):
    """
    根据仓库ID获取仓库详细信息

    Args:
        repository_id: 仓库ID
        db: 数据库会话
        include_tasks: 是否包含分析任务信息(默认False以提升性能)

    Returns:
        JSON响应包含仓库详细信息
    """
    try:
        # 获取仓库信息
        result = RepositoryService.get_repository_by_id(repository_id, db, include_tasks=include_tasks)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        if not result.get("repository"):
            return JSONResponse(status_code=404, content=result)

        # 如果成功获取到仓库信息，处理路径转换
        if result["status"] == "success" and result.get("repository"):
            repository = result["repository"]
            local_path = repository.get("local_path", "")

            # 检查是否为相对路径，如果是则转换为绝对路径
            if local_path and not os.path.isabs(local_path):
                # 相对路径转换为绝对路径
                # 获取当前文件的绝对路径，然后向上两级得到项目根目录
                current_file = os.path.abspath(__file__)  # backend/routers.py
                backend_dir = os.path.dirname(current_file)  # backend/
                project_root = os.path.dirname(backend_dir)  # Code-reader/

                # 数据库中存储的路径通常是相对于项目根目录的
                # 例如: ../data/repos/fcb4af8be6d3bc8f5da20e6c2e746b6b
                # 这个路径是相对于 backend/ 目录的，所以我们从 backend 目录开始解析
                absolute_path = os.path.abspath(os.path.join(backend_dir, local_path))

                repository["absolute_local_path"] = absolute_path
                logger.info(f"路径转换: {local_path} -> {absolute_path}")
                logger.info(f"项目根目录: {project_root}")
                logger.info(f"后端目录: {backend_dir}")
            else:
                repository["absolute_local_path"] = local_path

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取仓库信息时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )


@repository_router.get("/repositories")
async def get_repository_by_name_or_full_name(
    name: Optional[str] = Query(None, description="仓库名称（精确匹配）"),
    full_name: Optional[str] = Query(None, description="完整仓库名（精确匹配）"),
    db: Session = Depends(get_db),
):
    """
    根据仓库名称或完整仓库名精确查询仓库信息

    Args:
        name: 仓库名称（精确匹配，可选）
        full_name: 完整仓库名（精确匹配，可选）
        db: 数据库会话

    Returns:
        JSON响应包含仓库信息

    Note:
        name 和 full_name 至少需要提供一个参数
    """
    try:
        # 验证参数
        if not name and not full_name:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "请提供 name 或 full_name 参数进行查询",
                },
            )

        # 根据提供的参数进行查询
        if name and full_name:
            # 如果同时提供了两个参数，优先使用 full_name
            result = RepositoryService.get_repository_by_name_or_full_name(
                name=None, full_name=full_name, db=db, include_tasks=False
            )
            search_field = "full_name"
            search_value = full_name
        elif full_name:
            result = RepositoryService.get_repository_by_name_or_full_name(
                name=None, full_name=full_name, db=db, include_tasks=False
            )
            search_field = "full_name"
            search_value = full_name
        else:
            result = RepositoryService.get_repository_by_name_or_full_name(
                name=name, full_name=None, db=db, include_tasks=False
            )
            search_field = "name"
            search_value = name

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        if not result.get("repository"):
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "查询仓库信息时发生未知错误",
                "search_field": search_field if "search_field" in locals() else "unknown",
                "search_value": search_value if "search_value" in locals() else "unknown",
                "error": str(e),
            },
        )


@repository_router.post("/repositories")
async def create_repository(
    repository_data: RepositoryCreate,
    db: Session = Depends(get_db),
):
    """
    创建新仓库

    Args:
        repository_data: 仓库创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的仓库信息
    """
    try:
        # 转换为字典
        data_dict = repository_data.model_dump()

        # 创建仓库
        result = RepositoryService.create_repository(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建仓库时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.get("/repositories-list")
async def get_repositories_list(
    user_id: Optional[int] = Query(None, description="按用户ID筛选"),
    status: Optional[int] = Query(None, description="按状态筛选: 1=存在，0=已删除"),
    order_by: str = Query(
        "created_at", description="排序字段: id, user_id, name, full_name, status, created_at, updated_at"
    ),
    order_direction: str = Query("desc", description="排序方向: asc, desc"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量，1-100"),
    db: Session = Depends(get_db),
):
    """
    获取仓库列表，支持筛选、排序和分页

    Args:
        user_id: 用户ID筛选（可选）
        status: 状态筛选（可选）
        order_by: 排序字段
        order_direction: 排序方向
        page: 页码
        page_size: 每页数量
        db: 数据库会话

    Returns:
        JSON响应包含仓库列表和分页信息
    """
    try:
        # 调用服务层方法
        result = RepositoryService.get_repositories_list(
            user_id=user_id,
            status=status,
            order_by=order_by,
            order_direction=order_direction,
            page=page,
            page_size=page_size,
            db=db,
        )

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取仓库列表时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.get("/analysis-tasks/{repository_id}")
async def get_analysis_tasks_by_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    order_by: str = Query(
        "start_time",
        description="排序字段: start_time, end_time, status, total_files, successful_files, failed_files, code_lines, module_count, id",
    ),
    order_direction: str = Query("asc", description="排序方向: asc, desc"),
):
    """
    根据仓库ID获取分析任务列表

    Args:
        repository_id: 仓库ID
        db: 数据库会话
        order_by: 排序字段
        order_direction: 排序方向

    Returns:
        JSON响应包含分析任务列表和统计信息
    """
    try:
        # 获取分析任务列表
        result = AnalysisTaskService.get_tasks_by_repository_id(repository_id, db, order_by, order_direction)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到分析任务
        if result["total_tasks"] == 0:
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取分析任务列表时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )


@repository_router.post("/analysis-tasks")
async def create_analysis_task(
    task_data: AnalysisTaskCreate,
    db: Session = Depends(get_db),
):
    """
    创建新的分析任务

    Args:
        task_data: 分析任务创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的分析任务信息
    """
    try:
        # 转换为字典
        data_dict = task_data.model_dump()

        # 创建分析任务
        result = AnalysisTaskService.create_analysis_task(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建分析任务时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.put("/analysis-tasks/{task_id}")
async def update_analysis_task(
    task_id: int,
    task_data: AnalysisTaskUpdate,
    db: Session = Depends(get_db),
):
    """
    更新分析任务信息

    Args:
        task_id: 分析任务ID
        task_data: 分析任务更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的分析任务信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = task_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "task_id": task_id,
                },
            )

        # 更新分析任务
        result = AnalysisTaskService.update_analysis_task(task_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新分析任务时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            },
        )


@repository_router.delete("/analysis-tasks/{task_id}")
async def delete_analysis_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    删除分析任务

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除分析任务
        result = AnalysisTaskService.delete_analysis_task(task_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除分析任务时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            },
        )


@repository_router.get("/analysis-tasks/detail/{task_id}")
async def get_analysis_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    获取指定分析任务的详细信息(包含数据模型分析进度)

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含分析任务的详细信息
    """
    try:
        # 查询分析任务
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到ID为 {task_id} 的分析任务",
                },
            )

        # 查询数据模型分析进度
        file_analyses = db.query(FileAnalysis).filter(FileAnalysis.task_id == task_id).all()
        analysis_total = len(file_analyses)
        analysis_success = sum(1 for f in file_analyses if f.status == 'success')
        analysis_pending = sum(1 for f in file_analyses if f.status == 'pending')
        analysis_failed = sum(1 for f in file_analyses if f.status == 'failed')

        # 计算进度百分比
        vectorize_progress = 0
        if task.total_files and task.total_files > 0:
            vectorize_progress = round((task.successful_files / task.total_files) * 100)

        analysis_progress = 0
        if analysis_total > 0:
            analysis_progress = round((analysis_success / analysis_total) * 100)

        # 返回任务信息(包含两个阶段的进度)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "获取分析任务信息成功",
                "task": {
                    "id": task.id,
                    "status": task.status,
                    "current_file": task.current_file,
                    "start_time": task.start_time.isoformat() if task.start_time else None,
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    # 向量化阶段进度
                    "total_files": task.total_files or 0,
                    "successful_files": task.successful_files or 0,
                    "failed_files": task.failed_files or 0,
                    "vectorize_progress": vectorize_progress,
                    # 数据模型分析阶段进度
                    "analysis_total_files": analysis_total,
                    "analysis_success_files": analysis_success,
                    "analysis_pending_files": analysis_pending,
                    "analysis_failed_files": analysis_failed,
                    "analysis_progress": analysis_progress,
                    "task_index": task.task_index,
                    # 关键指标
                    "code_lines": task.code_lines or 0,
                    "module_count": task.module_count or 0,
                    # DeepWiki 文档生成任务 ID
                    "deepwiki_task_id": task.deepwiki_task_id,
                },
            },
        )

    except Exception as e:
        logger.error(f"获取分析任务信息时发生错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取分析任务信息时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.get("/analysis-tasks/{task_id}/can-start")
async def can_start_analysis_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    判断分析任务是否可以开启

    判断指定的任务ID是否满足开启条件：
    1. 当前没有状态为 running 的任务
    2. 指定的 task_id 在状态为 pending 的任务中是 start_time 最早的

    Args:
        task_id: 要判断的任务ID
        db: 数据库会话

    Returns:
        JSON响应包含判断结果：
        - can_start: boolean，是否可以开启
        - reason: string，判断原因
        - 其他相关信息
    """
    try:
        # 判断任务是否可以开启
        result = AnalysisTaskService.can_start_task(task_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"判断任务是否可以开启时发生错误: {str(e)}",
                "task_id": task_id,
                "can_start": False,
                "error": str(e),
            },
        )


@repository_router.get("/analysis-tasks/queue/status")
async def get_queue_status(
    db: Session = Depends(get_db),
):
    """
    获取任务队列状态

    Args:
        db: 数据库会话

    Returns:
        JSON响应包含队列状态信息
    """
    try:
        # 获取队列状态
        result = AnalysisTaskService.get_queue_status(db)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取队列状态时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.get("/files/{task_id}")
async def get_repository_files(
    task_id: int,
    db: Session = Depends(get_db),
    language: Optional[str] = Query(None, description="按编程语言过滤"),
    analysis_version: Optional[str] = Query(None, description="按分析版本过滤"),
    status: Optional[str] = Query(None, description="按分析状态过滤: pending, success, failed"),
    include_code_content: bool = Query(False, description="是否返回代码内容"),
):
    """
    获取指定任务ID的仓库文件列表

    Args:
        task_id: 任务ID
        db: 数据库会话
        language: 编程语言过滤器
        analysis_version: 分析版本过滤器
        status: 状态过滤器
        include_code_content: 是否返回代码内容

    Returns:
        JSON响应包含文件列表
    """
    try:
        # 获取文件列表
        result = FileAnalysisService.get_files_by_task_id(
            task_id,
            db,
            language=language,
            analysis_version=analysis_version,
            status=status,
            include_code_content=include_code_content,
        )

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到文件
        if result["total_files"] == 0:
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "获取文件列表时发生未知错误", "task_id": task_id, "error": str(e)},
        )


@repository_router.get("/file-analysis/{file_id}")
async def get_file_analysis_by_id(
    file_id: int,
    task_id: int = Query(..., description="任务ID"),
    db: Session = Depends(get_db),
):
    """
    根据文件分析ID和任务ID获取单条文件分析记录的完整内容

    Args:
        file_id: 文件分析记录ID
        task_id: 任务ID
        db: 数据库会话

    Returns:
        JSON响应包含完整的文件分析记录
    """
    try:
        # 获取文件分析记录
        result = FileAnalysisService.get_file_analysis_by_id_and_task_id(file_id, task_id, db)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到记录
        if not result.get("file_analysis"):
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取文件分析记录时发生未知错误",
                "file_id": file_id,
                "task_id": task_id,
                "error": str(e),
            },
        )


@repository_router.post("/file-analysis")
async def create_file_analysis(
    file_data: FileAnalysisCreate,
    db: Session = Depends(get_db),
):
    """
    创建新的文件分析记录

    Args:
        file_data: 文件分析创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的文件分析记录信息
    """
    try:
        # 转换为字典
        data_dict = file_data.model_dump()

        # 创建文件分析记录
        result = FileAnalysisService.create_file_analysis(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建文件分析记录时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.put("/file-analysis/{file_id}")
async def update_file_analysis(
    file_id: int,
    file_data: FileAnalysisUpdate,
    db: Session = Depends(get_db),
):
    """
    更新文件分析记录信息

    Args:
        file_id: 文件分析记录ID
        file_data: 文件分析更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的文件分析记录信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = file_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "file_id": file_id,
                },
            )

        # 更新文件分析记录
        result = FileAnalysisService.update_file_analysis(file_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新文件分析记录时发生未知错误",
                "file_id": file_id,
                "error": str(e),
            },
        )


@repository_router.delete("/file-analysis/{file_id}")
async def delete_file_analysis(
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    删除文件分析记录

    Args:
        file_id: 文件分析记录ID
        db: 数据库会话

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除文件分析记录
        result = FileAnalysisService.delete_file_analysis(file_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除文件分析记录时发生未知错误",
                "file_id": file_id,
                "error": str(e),
            },
        )


@repository_router.get("/analysis-items/{file_analysis_id}")
async def get_file_analysis_items(
    file_analysis_id: int,
    db: Session = Depends(get_db),
    target_type: Optional[str] = Query(None, description="按目标类型过滤: file, class, function"),
    language: Optional[str] = Query(None, description="按编程语言过滤"),
):
    """
    获取指定文件分析ID的分析项详细内容

    Args:
        file_analysis_id: 文件分析ID
        db: 数据库会话
        target_type: 目标类型过滤器 (file/class/function)
        language: 编程语言过滤器

    Returns:
        JSON响应包含分析项列表，按start_line升序排序
    """
    try:
        # 获取分析项列表
        result = AnalysisItemService.get_analysis_items_by_file_id(
            file_analysis_id, db, target_type=target_type, language=language
        )

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 即使没有分析项也返回200，因为这是正常情况（文件可能还在分析中或确实没有可分析的内容）
        # 404应该只用于file_analysis_id本身不存在的情况
        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取分析项列表时发生未知错误",
                "file_analysis_id": file_analysis_id,
                "error": str(e),
            },
        )


@repository_router.post("/analysis-items")
async def create_analysis_item(
    item_data: AnalysisItemCreate,
    db: Session = Depends(get_db),
):
    """
    创建新的分析项记录

    Args:
        item_data: 分析项创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的分析项记录信息
    """
    try:
        # 转换为字典
        data_dict = item_data.model_dump()

        # 创建分析项记录
        result = AnalysisItemService.create_analysis_item(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建分析项记录时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.put("/analysis-items/{item_id}")
async def update_analysis_item(
    item_id: int,
    item_data: AnalysisItemUpdate,
    db: Session = Depends(get_db),
):
    """
    更新分析项记录信息

    Args:
        item_id: 分析项记录ID
        item_data: 分析项更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的分析项记录信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = item_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "item_id": item_id,
                },
            )

        # 更新分析项记录
        result = AnalysisItemService.update_analysis_item(item_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新分析项记录时发生未知错误",
                "item_id": item_id,
                "error": str(e),
            },
        )


@repository_router.delete("/analysis-items/{item_id}")
async def delete_analysis_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """
    删除分析项记录

    Args:
        item_id: 分析项记录ID
        db: 数据库会话

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除分析项记录
        result = AnalysisItemService.delete_analysis_item(item_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除分析项记录时发生未知错误",
                "item_id": item_id,
                "error": str(e),
            },
        )


@repository_router.post("/upload")
async def upload_repository(
    files: List[UploadFile] = File(...),
    repository_name: str = Form(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    上传完整的仓库文件夹

    接收前端上传的整个项目文件夹，保持完整的目录结构，
    并提供详细的文件夹结构分析和统计信息。
    上传成功后会自动创建分析任务并触发分析流程。

    Args:
        files: 上传的文件列表（包含完整文件夹结构）
        repository_name: 仓库名称
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        JSON响应包含：
        - 上传结果和仓库信息
        - 文件夹结构分析
        - 文件类型统计
        - 项目特征识别
        - 分析任务ID
    """
    try:
        # 调用上传服务
        result = await UploadService.upload_repository_files(files, repository_name, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        # 如果上传成功且创建了任务，自动触发分析
        task_id = result.get("task_id")
        repository_id = result.get("repository_id")
        local_path = result.get("local_path")

        if task_id and repository_id and local_path and background_tasks:
            # 获取仓库信息
            repository = db.query(Repository).filter(Repository.id == repository_id).first()
            if repository:
                repo_info = {
                    "full_name": repository.full_name or repository.name,
                    "name": repository.name,
                    "local_path": repository.local_path,
                }

                # 在后台自动触发分析流程
                async def run_analysis_pipeline():
                    """后台运行完整的分析流程"""
                    import sys
                    from pathlib import Path

                    # 添加项目根目录到Python路径
                    project_root = Path(__file__).parent.parent
                    if str(project_root) not in sys.path:
                        sys.path.insert(0, str(project_root))

                    try:
                        from src.flows.web_flow import create_knowledge_base as create_kb_flow
                        from src.flows.web_flow import analyze_data_model as analyze_dm_flow

                        # 创建新的数据库会话
                        from database import SessionLocal
                        db_session = SessionLocal()

                        try:
                            # 更新任务状态为运行中
                            task = db_session.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                            if task:
                                task.status = "running"
                                db_session.commit()

                            # 步骤1: 创建知识库
                            logger.info(f"[任务 {task_id}] 开始创建知识库...")
                            kb_result = await create_kb_flow(
                                task_id=task_id,
                                local_path=local_path,
                                repo_info=repo_info
                            )

                            if kb_result.get("status") != "knowledge_base_ready":
                                logger.error(f"[任务 {task_id}] 知识库创建失败: {kb_result}")
                                task = db_session.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                                if task:
                                    task.status = "failed"
                                    db_session.commit()
                                return

                            logger.info(f"[任务 {task_id}] 知识库创建成功")

                            # 获取向量索引名称
                            vectorstore_index = kb_result.get("vectorstore_index")
                            if not vectorstore_index:
                                logger.error(f"[任务 {task_id}] 知识库创建成功但未返回向量索引")
                                task = db_session.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                                if task:
                                    task.status = "failed"
                                    db_session.commit()
                                return

                            # 步骤2: 分析数据模型
                            logger.info(f"[任务 {task_id}] 开始分析数据模型...")
                            dm_result = await analyze_dm_flow(
                                task_id=task_id,
                                vectorstore_index=vectorstore_index
                            )

                            if dm_result.get("status") == "completed":
                                logger.info(f"[任务 {task_id}] 数据模型分析成功")
                            else:
                                logger.error(f"[任务 {task_id}] 数据模型分析失败: {dm_result}")

                        finally:
                            db_session.close()

                    except Exception as e:
                        logger.error(f"[任务 {task_id}] 分析流程执行失败: {str(e)}")
                        # 更新任务状态为失败
                        from database import SessionLocal
                        db_session = SessionLocal()
                        try:
                            task = db_session.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                            if task:
                                task.status = "failed"
                                db_session.commit()
                        finally:
                            db_session.close()

                # 添加后台任务
                background_tasks.add_task(run_analysis_pipeline)
                logger.info(f"✅ 已添加后台分析任务: 任务ID={task_id}, 仓库ID={repository_id}")

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "上传仓库文件时发生未知错误",
                "repository_name": repository_name,
                "error": str(e),
            },
        )


@analysis_router.post("/repository/{repository_id}/reanalyze")
async def reanalyze_repository(
    repository_id: int,
    db: Session = Depends(get_db),
):
    """
    重新分析已有仓库（使用 Celery 异步任务）

    为已上传的仓库创建新的分析任务并自动开始分析流程

    Args:
        repository_id: 仓库ID
        db: 数据库会话

    Returns:
        JSON响应包含新创建的任务信息
    """
    try:
        # 验证仓库是否存在
        repository = db.query(Repository).filter(Repository.id == repository_id).first()
        if not repository:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到ID为 {repository_id} 的仓库",
                    "repository_id": repository_id,
                },
            )

        # 检查仓库路径是否存在
        repo_path = os.path.join(os.getcwd(), repository.local_path)
        if not os.path.exists(repo_path):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"仓库路径不存在: {repo_path}",
                    "repository_id": repository_id,
                },
            )

        # ========== 检查是否有可恢复的失败任务 ==========
        failed_task = db.query(AnalysisTask).filter(
            AnalysisTask.repository_id == repository_id,
            AnalysisTask.status == 'failed'
        ).order_by(AnalysisTask.id.desc()).first()

        # 如果有失败任务且向量化已完成（有 task_index），恢复该任务
        # 不管 successful_files 是否 > 0，只要向量化完成就可以恢复
        if failed_task and failed_task.task_index:
            logger.info(f"🔄 发现可恢复的失败任务 {failed_task.id}，已完成 {failed_task.successful_files}/{failed_task.total_files} 个文件")

            # 停止正在运行的任务
            running_tasks = db.query(AnalysisTask).filter(
                AnalysisTask.repository_id == repository_id,
                AnalysisTask.status.in_(['running', 'pending'])
            ).all()

            if running_tasks:
                from tasks import celery_app

                for old_task in running_tasks:
                    logger.info(f"⚠️ 发现仓库 {repository_id} 的旧任务 {old_task.id}（状态: {old_task.status}），准备停止")

                    # 尝试找到并撤销对应的 Celery 任务
                    try:
                        inspect = celery_app.control.inspect()
                        active_tasks = inspect.active()

                        if active_tasks:
                            for worker, tasks in active_tasks.items():
                                for task in tasks:
                                    if task['name'] == 'tasks.run_analysis_task':
                                        task_args = task.get('args', [])
                                        if task_args and len(task_args) > 0 and task_args[0] == old_task.id:
                                            celery_task_id = task['id']
                                            celery_app.control.revoke(celery_task_id, terminate=True, signal='SIGKILL')
                                            logger.info(f"✅ 已撤销 Celery 任务 {celery_task_id[:8]}... (对应任务 {old_task.id})")
                    except Exception as e:
                        logger.warning(f"撤销 Celery 任务时出错: {str(e)}")

                    old_task.status = 'cancelled'
                    logger.info(f"✅ 已将任务 {old_task.id} 状态更新为 cancelled")

                db.commit()
                logger.info(f"✅ 已停止仓库 {repository_id} 的 {len(running_tasks)} 个旧任务")

            # 恢复失败任务
            # 检查是否还有未完成的文件
            remaining_files = failed_task.total_files - failed_task.successful_files

            if remaining_files > 0:
                # 还有文件未完成，重新提交任务
                failed_task.status = 'pending'
                failed_task.end_time = None
                db.commit()

                logger.info(f"✅ 恢复任务 {failed_task.id}，将继续分析剩余的 {remaining_files} 个文件")

                # 提交到 Celery
                from tasks import run_analysis_task
                run_analysis_task.delay(failed_task.id, repository.local_path)

                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": f"已恢复任务 {failed_task.id}，继续分析剩余的 {remaining_files} 个文件",
                        "task": {
                            "id": failed_task.id,
                            "repository_id": repository_id,
                            "status": failed_task.status,
                            "total_files": failed_task.total_files,
                            "successful_files": failed_task.successful_files,
                            "failed_files": failed_task.failed_files,
                        },
                    },
                )
            else:
                # 所有文件都已完成，直接标记为完成
                failed_task.status = 'completed'
                failed_task.end_time = datetime.now()
                db.commit()

                logger.info(f"✅ 任务 {failed_task.id} 所有文件已完成，标记为完成")

                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": f"任务 {failed_task.id} 已完成",
                        "task": {
                            "id": failed_task.id,
                            "repository_id": repository_id,
                            "status": failed_task.status,
                            "total_files": failed_task.total_files,
                            "successful_files": failed_task.successful_files,
                            "failed_files": failed_task.failed_files,
                        },
                    },
                )

        # ========== 停止正在运行的任务 ==========
        running_tasks = db.query(AnalysisTask).filter(
            AnalysisTask.repository_id == repository_id,
            AnalysisTask.status.in_(['running', 'pending'])
        ).all()

        if running_tasks:
            from tasks import celery_app

            for old_task in running_tasks:
                logger.info(f"⚠️ 发现仓库 {repository_id} 的旧任务 {old_task.id}（状态: {old_task.status}），准备停止")

                # 尝试找到并撤销对应的 Celery 任务
                try:
                    inspect = celery_app.control.inspect()
                    active_tasks = inspect.active()

                    if active_tasks:
                        for worker, tasks in active_tasks.items():
                            for task in tasks:
                                if task['name'] == 'tasks.run_analysis_task':
                                    task_args = task.get('args', [])
                                    if task_args and len(task_args) > 0 and task_args[0] == old_task.id:
                                        celery_task_id = task['id']
                                        celery_app.control.revoke(celery_task_id, terminate=True, signal='SIGKILL')
                                        logger.info(f"✅ 已撤销 Celery 任务 {celery_task_id[:8]}... (对应任务 {old_task.id})")
                except Exception as e:
                    logger.warning(f"撤销 Celery 任务时出错: {str(e)}")

                old_task.status = 'cancelled'
                logger.info(f"✅ 已将任务 {old_task.id} 状态更新为 cancelled")

            db.commit()
            logger.info(f"✅ 已停止仓库 {repository_id} 的 {len(running_tasks)} 个旧任务")

        # 创建新的分析任务
        new_task = AnalysisTask(
            repository_id=repository_id,
            status="pending",
            total_files=0,
            successful_files=0,
            failed_files=0,
            code_lines=0,
            module_count=0,
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        logger.info(f"为仓库 {repository_id} 创建了新的分析任务 {new_task.id}")

        # 准备仓库信息
        repo_info = {
            "full_name": repository.full_name or repository.name,
            "name": repository.name,
            "local_path": repository.local_path,
        }

        # 使用 Celery 异步任务执行分析流程
        from tasks import run_analysis_task

        celery_task = run_analysis_task.delay(new_task.id, repo_info)

        logger.info(f"已提交任务 {new_task.id} 到 Celery 队列 (Celery任务ID: {celery_task.id})")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "重新分析任务已创建并提交到后台队列",
                "repository_id": repository_id,
                "task_id": new_task.id,
                "repository_name": repository.name,
                "celery_task_id": celery_task.id,
            },
        )

    except Exception as e:
        logger.error(f"重新分析仓库失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "重新分析仓库时发生错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )


@analysis_router.post("/{task_id}/create-knowledge-base")
async def create_knowledge_base(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    为指定任务创建知识库

    触发知识库创建flow，包含向量化和数据库更新

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含知识库创建状态和进度信息
    """
    try:
        # 验证任务是否存在
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到ID为 {task_id} 的分析任务",
                    "task_id": task_id,
                },
            )

        # 获取仓库信息
        repository = db.query(Repository).filter(Repository.id == task.repository_id).first()
        if not repository:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到仓库ID为 {task.repository_id} 的仓库",
                    "task_id": task_id,
                },
            )

        # 检查任务状态
        if task.status not in ["pending", "running"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"任务状态为 {task.status}，无法创建知识库",
                    "task_id": task_id,
                },
            )

        # 准备仓库信息
        repo_info = {
            "full_name": repository.full_name or repository.name,
            "name": repository.name,
            "local_path": repository.local_path,
        }

        # 启动知识库创建flow（异步执行）
        import asyncio
        import sys
        from pathlib import Path

        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        try:
            from src.flows.web_flow import create_knowledge_base as create_kb_flow
        except ImportError as e:
            logger.error(f"导入知识库创建flow失败: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"导入知识库创建flow失败: {str(e)}",
                    "task_id": task_id,
                },
            )

        # 更新任务状态为运行中
        task.status = "running"
        db.commit()

        # 同步执行知识库创建flow，等待完成后返回结果
        try:
            logger.info(f"开始执行知识库创建flow，任务ID: {task_id}")
            result = await create_kb_flow(task_id=task_id, local_path=repository.local_path, repo_info=repo_info)

            # 检查flow执行结果
            if result.get("status") == "knowledge_base_ready" and result.get("vectorstore_index"):
                logger.info(f"知识库创建成功，索引: {result.get('vectorstore_index')}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "知识库创建完成",
                        "task_id": task_id,
                        "task_status": "running",  # 保持running状态，等待后续步骤
                        "vectorstore_index": result.get("vectorstore_index"),
                    },
                )
            else:
                logger.error(f"知识库创建失败: {result}")
                # 回滚任务状态
                task.status = "failed"
                db.commit()
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": f"知识库创建失败: {result.get('error', '未知错误')}",
                        "task_id": task_id,
                    },
                )

        except Exception as e:
            logger.error(f"执行知识库创建flow失败: {str(e)}")
            # 回滚任务状态
            task.status = "failed"
            db.commit()
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"执行知识库创建flow失败: {str(e)}",
                    "task_id": task_id,
                },
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "启动知识库创建时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            },
        )


@analysis_router.post("/{task_id}/analyze-data-model")
async def analyze_data_model(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    为指定任务执行分析数据模型

    触发分析数据模型flow，包含代码分析和数据库更新

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含分析数据模型状态和进度信息
    """
    try:
        # 验证任务是否存在
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到ID为 {task_id} 的分析任务",
                    "task_id": task_id,
                },
            )

        # 获取仓库信息
        repository = db.query(Repository).filter(Repository.id == task.repository_id).first()
        if not repository:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到仓库ID为 {task.repository_id} 的仓库",
                    "task_id": task_id,
                },
            )

        # 检查任务状态
        if task.status not in ["pending", "running", "completed"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"任务状态为 {task.status}，无法执行分析数据模型",
                    "task_id": task_id,
                },
            )

        # 检查是否有知识库索引
        if not task.task_index:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "任务缺少知识库索引，请先完成知识库创建",
                    "task_id": task_id,
                },
            )

        # 启动分析数据模型flow（异步执行）
        import sys
        from pathlib import Path

        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        try:
            from src.flows.web_flow import analyze_data_model as analyze_dm_flow
        except ImportError as e:
            logger.error(f"导入分析数据模型flow失败: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"导入分析数据模型flow失败: {str(e)}",
                    "task_id": task_id,
                },
            )

        # 更新任务状态为运行中
        task.status = "running"
        db.commit()

        try:
            logger.info(f"开始执行分析数据模型flow，任务ID: {task_id}")
            result = await analyze_dm_flow(task_id=task_id, vectorstore_index=task.task_index)

            # 检查flow执行结果
            if result.get("status") == "analysis_completed":
                analysis_items_count = result.get("analysis_items_count", 0)
                total_files = result.get("total_files", 0)
                successful_files = result.get("successful_files", 0)
                failed_files = result.get("failed_files", 0)
                success_rate = result.get("success_rate", "0%")

                logger.info(
                    f"分析数据模型完成: 总文件 {total_files}, 成功 {successful_files}, 失败 {failed_files}, 分析项 {analysis_items_count}"
                )

                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": result.get("message", "分析数据模型完成"),
                        "task_id": task_id,
                        "task_status": "running",  # 保持running状态，等待后续步骤
                        "analysis_items_count": analysis_items_count,
                        "total_files": total_files,
                        "successful_files": successful_files,
                        "failed_files": failed_files,
                        "success_rate": success_rate,
                        "analysis_results": result.get("analysis_results", []),
                    },
                )
            else:
                logger.error(f"分析数据模型失败: {result}")
                # 回滚任务状态
                task.status = "failed"
                db.commit()
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": f"分析数据模型失败: {result.get('error', '未知错误')}",
                        "task_id": task_id,
                        "error_details": result.get("message", ""),
                    },
                )

        except Exception as e:
            logger.error(f"执行分析数据模型flow失败: {str(e)}")
            # 回滚任务状态
            task.status = "failed"
            db.commit()
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"执行分析数据模型flow失败: {str(e)}",
                    "task_id": task_id,
                },
            )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "启动分析数据模型时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            },
        )


@analysis_router.post("/file/{file_id}/analyze-data-model")
async def analyze_single_file_data_model(
    file_id: int,
    task_index: str = Query(..., description="任务索引"),
    task_id: Optional[int] = Query(None, description="任务ID（可选，如果不提供则从文件分析记录中获取）"),
    db: Session = Depends(get_db),
):
    """
    为指定文件执行分析数据模型

    触发单文件分析数据模型flow，包含代码分析和数据库更新

    Args:
        file_id: 文件分析ID
        task_index: 任务索引（知识库索引）
        db: 数据库会话

    Returns:
        JSON响应包含分析数据模型状态和进度信息
    """
    try:
        # 验证文件分析记录是否存在
        # FileAnalysis已经在文件顶部导入了，不需要重复导入

        file_analysis = db.query(FileAnalysis).filter(FileAnalysis.id == file_id).first()
        if not file_analysis:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到ID为 {file_id} 的文件分析记录",
                    "file_id": file_id,
                },
            )

        # 获取关联的任务信息
        task = db.query(AnalysisTask).filter(AnalysisTask.id == file_analysis.task_id).first()
        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到任务ID为 {file_analysis.task_id} 的分析任务",
                    "file_id": file_id,
                },
            )

        # 获取仓库信息
        repository = db.query(Repository).filter(Repository.id == task.repository_id).first()
        if not repository:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到仓库ID为 {task.repository_id} 的仓库",
                    "file_id": file_id,
                },
            )

        # 检查文件分析状态
        if file_analysis.status == "failed":
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"文件分析状态为 {file_analysis.status}，无法执行分析数据模型",
                    "file_id": file_id,
                },
            )

        # 启动单文件分析数据模型flow（异步执行）
        import sys
        from pathlib import Path

        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        try:
            from src.flows.web_flow import analyze_single_file_data_model as analyze_single_file_flow
        except ImportError as e:
            logger.error(f"导入单文件分析数据模型flow失败: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"导入单文件分析数据模型flow失败: {str(e)}",
                    "file_id": file_id,
                },
            )

        # 使用传递的task_id或从数据库获取的task_id
        actual_task_id = task_id if task_id is not None else task.id

        # 使用Celery异步任务处理分析
        celery_task = analyze_single_file_task.delay(
            task_id=actual_task_id,
            file_id=file_id,
            vectorstore_index=task_index
        )

        # 立即返回,不等待分析完成
        logger.info(f"已提交文件 {file_id} 到Celery任务队列 (Celery任务ID: {celery_task.id})")
        return JSONResponse(
            status_code=202,  # 202 Accepted - 请求已接受,正在处理
            content={
                "status": "accepted",
                "message": "单文件分析数据模型已提交到任务队列,正在后台执行",
                "file_id": file_id,
                "file_path": file_analysis.file_path,
                "celery_task_id": celery_task.id,
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "启动单文件分析数据模型时发生未知错误",
                "file_id": file_id,
                "error": str(e),
            },
        )


@repository_router.put("/repositories/{repository_id}")
async def update_repository(
    repository_id: int,
    repository_data: RepositoryUpdate,
    db: Session = Depends(get_db),
):
    """
    更新仓库信息

    Args:
        repository_id: 仓库ID
        repository_data: 仓库更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的仓库信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = repository_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "repository_id": repository_id,
                },
            )

        # 更新仓库
        result = RepositoryService.update_repository(repository_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新仓库时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )


@repository_router.delete("/repositories/{repository_id}")
async def delete_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    soft_delete: bool = Query(True, description="是否软删除（True=设置status为0，False=物理删除）"),
):
    """
    删除仓库（支持软删除和硬删除）

    Args:
        repository_id: 仓库ID
        db: 数据库会话
        soft_delete: 是否软删除

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除仓库
        result = RepositoryService.delete_repository(repository_id, db, soft_delete=soft_delete)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除仓库时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )


# Task README 相关路由
@repository_router.post("/task-readmes")
async def create_task_readme(
    readme_data: TaskReadmeCreate,
    db: Session = Depends(get_db),
):
    """
    创建任务README

    Args:
        readme_data: README创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的README信息
    """
    try:
        # 转换为字典
        data_dict = readme_data.model_dump()

        # 创建README
        result = TaskReadmeService.create_task_readme(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建README时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.get("/task-readmes/{readme_id}")
async def get_task_readme_by_id(
    readme_id: int,
    db: Session = Depends(get_db),
):
    """
    根据README ID获取README详细信息

    Args:
        readme_id: README ID
        db: 数据库会话

    Returns:
        JSON响应包含README详细信息
    """
    try:
        # 获取README信息
        result = TaskReadmeService.get_task_readme_by_id(readme_id, db)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        if not result.get("readme"):
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取README信息时发生未知错误",
                "readme_id": readme_id,
                "error": str(e),
            },
        )


@repository_router.get("/task-readmes/by-task/{task_id}")
async def get_task_readme_by_task_id(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    根据任务ID获取README信息

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        JSON响应包含README信息
    """
    try:
        # 获取README信息
        result = TaskReadmeService.get_task_readme_by_task_id(task_id, db)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有 README，返回空数据而不是 404
        if not result.get("readme"):
            return JSONResponse(status_code=200, content={
                "status": "success",
                "message": "该任务暂无README数据",
                "task_id": task_id,
                "readme": None
            })

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取README信息时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            },
        )


@repository_router.put("/task-readmes/{readme_id}")
async def update_task_readme(
    readme_id: int,
    readme_data: TaskReadmeUpdate,
    db: Session = Depends(get_db),
):
    """
    更新README信息

    Args:
        readme_id: README ID
        readme_data: README更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的README信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = readme_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "readme_id": readme_id,
                },
            )

        # 更新README
        result = TaskReadmeService.update_task_readme(readme_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新README时发生未知错误",
                "readme_id": readme_id,
                "error": str(e),
            },
        )


@repository_router.delete("/task-readmes/{readme_id}")
async def delete_task_readme(
    readme_id: int,
    db: Session = Depends(get_db),
):
    """
    删除README

    Args:
        readme_id: README ID
        db: 数据库会话

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除README
        result = TaskReadmeService.delete_task_readme(readme_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除README时发生未知错误",
                "readme_id": readme_id,
                "error": str(e),
            },
        )


@repository_router.post("/upload/compress-and-upload/{md5_folder_name}")
async def compress_and_upload_folder(
    md5_folder_name: str,
    db: Session = Depends(get_db),
):
    """
    将指定md5文件夹压缩成zip文件并上传到README API服务

    Args:
        md5_folder_name: md5文件夹名称
        db: 数据库会话

    Returns:
        JSON响应包含压缩和上传结果
    """
    try:
        from config import Settings
        import tempfile

        # 构建文件夹路径
        folder_path = os.path.join(Settings.LOCAL_REPO_PATH, md5_folder_name)

        if not os.path.exists(folder_path):
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"文件夹不存在: {folder_path}"
                }
            )

        # 创建临时zip文件
        with tempfile.NamedTemporaryFile(suffix=f"_{md5_folder_name}.zip", delete=False) as temp_file:
            zip_path = temp_file.name

        # 压缩文件夹
        compress_success = UploadService.create_zip_from_folder(folder_path, zip_path)

        if not compress_success:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "压缩文件夹失败"
                }
            )

        # 上传到README API
        upload_result = await UploadService.upload_zip_to_readme_api(
            zip_path,
            Settings.README_API_BASE_URL
        )



        # 清理临时文件
        try:
            os.unlink(zip_path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

        if upload_result["success"]:
            # 自动触发分析任务（带去重检查）
            try:
                from tasks import run_analysis_task
                from models import AnalysisTask, Repository

                # 查找对应的仓库和任务
                repo = db.query(Repository).filter(Repository.local_path.like(f"%{md5_folder_name}%")).first()
                if repo:
                    # ✅ 先检查是否已有正在运行的任务（只检查 running 状态，不检查 pending）
                    running_task = db.query(AnalysisTask).filter(
                        AnalysisTask.repository_id == repo.id,
                        AnalysisTask.status == 'running'
                    ).first()

                    if running_task:
                        logger.info(f"⚠️ 仓库 {repo.id} 已有任务 {running_task.id} 正在运行（状态: {running_task.status}），跳过自动触发")
                    else:
                        # 查找最新的pending任务
                        task = db.query(AnalysisTask).filter(
                            AnalysisTask.repository_id == repo.id,
                            AnalysisTask.status == 'pending'
                        ).order_by(AnalysisTask.id.desc()).first()

                        if task:
                            # 提交Celery任务
                            celery_task = run_analysis_task.delay(
                                task_id=task.id,
                                external_file_path=repo.local_path
                            )
                            logger.info(f"✅ 自动触发分析任务: 任务ID {task.id}, Celery任务ID: {celery_task.id}")
            except Exception as e:
                logger.error(f"自动触发分析任务失败: {e}")

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "压缩和上传成功",
                    "md5_folder_name": md5_folder_name,
                    "upload_result": upload_result["data"]
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"上传失败: {upload_result['message']}",
                    "md5_folder_name": md5_folder_name
                }
            )

    except Exception as e:
        logger.error(f"压缩和上传过程中发生错误: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "压缩和上传过程中发生未知错误",
                "md5_folder_name": md5_folder_name,
                "error": str(e)
            }
        )


@repository_router.get("/analysis-tasks/{task_id}/mermaid-diagrams")
async def get_mermaid_diagrams(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    获取指定分析任务的 Mermaid 图表

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含 Mermaid 格式的类图、依赖图和流程图
    """
    try:
        from utils.mermaid_generator import MermaidGenerator
        from models import AnalysisItem

        # 查询分析任务
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"分析任务 {task_id} 不存在"
                }
            )

        # 获取所有文件分析（通过 task_id）
        file_analyses = db.query(FileAnalysis).filter(
            FileAnalysis.task_id == task_id
        ).all()

        if not file_analyses:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "未找到文件分析结果"
                }
            )

        # 获取所有分析项
        analysis_items = []
        file_analyses_data = []

        for file_analysis in file_analyses:
            # 获取该文件的所有分析项
            items = db.query(AnalysisItem).filter(
                AnalysisItem.file_analysis_id == file_analysis.id
            ).all()

            for item in items:
                analysis_items.append(item.to_dict())

            # 收集文件分析数据（用于依赖图）
            file_analyses_data.append({
                "file_path": file_analysis.file_path,
                "dependencies": []  # TODO: 从代码中提取依赖关系
            })

        # 生成所有图表
        diagrams = MermaidGenerator.generate_all_diagrams(
            analysis_items=analysis_items,
            file_analyses=file_analyses_data
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "diagrams": diagrams,
                "stats": {
                    "total_items": len(analysis_items),
                    "total_files": len(file_analyses),
                    "diagram_count": len(diagrams)
                }
            }
        )

    except Exception as e:
        logger.error(f"生成 Mermaid 图表失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"生成 Mermaid 图表失败: {str(e)}"
            }
        )


@repository_router.get("/analysis-tasks/{task_id}/quality-report")
async def get_quality_report(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    获取指定分析任务的代码质量报告

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含代码质量分析结果
    """
    try:
        from utils.code_quality_analyzer import CodeQualityAnalyzer

        # 查询分析任务
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"分析任务 {task_id} 不存在"
                }
            )

        # 获取所有文件分析
        file_analyses = db.query(FileAnalysis).filter(
            FileAnalysis.task_id == task_id
        ).all()

        if not file_analyses:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "未找到文件分析结果"
                }
            )

        # 分析每个文件的代码质量
        file_quality_results = []
        total_score = 0
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        language_stats = {}

        for file_analysis in file_analyses:
            # 只分析有代码内容的文件
            if not file_analysis.code_content:
                continue

            # 分析代码质量
            quality_result = CodeQualityAnalyzer.analyze_file_quality(
                file_path=file_analysis.file_path,
                code=file_analysis.code_content,
                language=file_analysis.language or "python"
            )

            # 只保留支持的语言
            if not quality_result.get("supported"):
                continue

            # 统计
            if "quality_score" in quality_result:
                total_score += quality_result["quality_score"]
                grade = quality_result.get("grade", "F")
                grade_counts[grade] = grade_counts.get(grade, 0) + 1

            # 语言统计
            lang = quality_result.get("language", "unknown")
            if lang not in language_stats:
                language_stats[lang] = {"count": 0, "total_score": 0}
            language_stats[lang]["count"] += 1
            language_stats[lang]["total_score"] += quality_result.get("quality_score", 0)

            # 简化结果（不包含详细的函数列表）
            simplified_result = {
                "file_path": quality_result["file_path"],
                "language": quality_result["language"],
                "quality_score": quality_result.get("quality_score", 0),
                "grade": quality_result.get("grade", "F"),
                "complexity_avg": quality_result.get("complexity", {}).get("average", 0),
                "maintainability_score": quality_result.get("maintainability", {}).get("score", 0),
                "comment_ratio": quality_result.get("comment_ratio", {}).get("ratio", 0),
            }

            file_quality_results.append(simplified_result)

        # 计算总体统计
        analyzed_files = len(file_quality_results)
        if analyzed_files == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "task_id": task_id,
                    "message": "没有可分析的文件（可能不支持该语言）",
                    "summary": {
                        "total_files": len(file_analyses),
                        "analyzed_files": 0
                    }
                }
            )

        average_score = total_score / analyzed_files

        # 计算语言平均分
        for lang, stats in language_stats.items():
            if stats["count"] > 0:
                stats["average_score"] = round(stats["total_score"] / stats["count"], 2)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "summary": {
                    "total_files": len(file_analyses),
                    "analyzed_files": analyzed_files,
                    "average_score": round(average_score, 2),
                    "overall_grade": CodeQualityAnalyzer._get_quality_grade(average_score),
                    "grade_distribution": grade_counts,
                    "language_stats": language_stats
                },
                "files": file_quality_results[:50]  # 限制返回前 50 个文件
            }
        )

    except Exception as e:
        logger.error(f"生成代码质量报告失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"生成代码质量报告失败: {str(e)}"
            }
        )


@repository_router.get("/analysis-tasks/{task_id}/dependencies")
async def get_dependencies_analysis(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    获取指定分析任务的依赖关系分析

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含依赖关系分析结果
    """
    try:
        from utils.dependency_analyzer import DependencyAnalyzer
        import json as json_lib

        # 查询分析任务
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"分析任务 {task_id} 不存在"
                }
            )

        # 获取所有文件分析
        file_analyses = db.query(FileAnalysis).filter(
            FileAnalysis.task_id == task_id
        ).all()

        if not file_analyses:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "未找到文件分析结果"
                }
            )

        # 提取每个文件的依赖关系
        file_dependencies = {}

        for file_analysis in file_analyses:
            # 如果数据库中已经存储了依赖关系，直接使用
            if file_analysis.dependencies:
                try:
                    deps = json_lib.loads(file_analysis.dependencies)
                    if isinstance(deps, list):
                        file_dependencies[file_analysis.file_path] = deps
                    continue
                except:
                    pass

            # 否则从代码中提取
            if file_analysis.code_content:
                deps = DependencyAnalyzer.extract_dependencies(
                    code=file_analysis.code_content,
                    language=file_analysis.language or "python"
                )
                file_dependencies[file_analysis.file_path] = deps

                # 更新数据库
                try:
                    file_analysis.dependencies = json_lib.dumps(deps)
                    db.commit()
                except Exception as e:
                    logger.warning(f"更新依赖关系失败: {e}")
                    db.rollback()

        # 分析依赖关系
        summary = DependencyAnalyzer.analyze_dependencies_summary(file_dependencies)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "summary": summary,
                "file_dependencies": {
                    k: v for k, v in list(file_dependencies.items())[:50]  # 限制返回前 50 个
                }
            }
        )

    except Exception as e:
        logger.error(f"依赖关系分析失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"依赖关系分析失败: {str(e)}"
            }
        )


@repository_router.post("/repositories/{repository_id}/init-claude-session")
async def init_claude_session(
    repository_id: int,
    db: Session = Depends(get_db)
):
    """
    初始化仓库的 Claude AI 会话

    如果仓库已有 claude_session_id，则直接返回
    如果没有，则打包代码并上传到 claude-agent-sdk 创建新会话
    """
    try:
        # 获取仓库信息
        repository = db.query(Repository).filter(Repository.id == repository_id).first()
        if not repository:
            raise HTTPException(status_code=404, detail="仓库不存在")

        # 如果已有 session_id，检查是否有效
        if repository.claude_session_id:
            # 验证 session 是否存在
            claude_api_url = os.getenv("CLAUDE_CHAT_API_BASE_URL", "http://localhost:8003")
            test_response = requests.post(
                f"{claude_api_url}/chat/{repository.claude_session_id}",
                json={"query": "test", "conversation_id": None},
                timeout=5
            )

            if test_response.status_code != 404:
                # Session 有效，直接返回
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "Claude session 已存在",
                        "session_id": repository.claude_session_id
                    }
                )

        # Session 不存在或无效，创建新的
        local_path = Path(repository.local_path)
        if not local_path.exists():
            raise HTTPException(status_code=404, detail=f"仓库路径不存在: {repository.local_path}")

        # 创建临时 zip 文件
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            zip_path = tmp_file.name

        try:
            # 打包代码库
            logger.info(f"正在打包代码库: {local_path}")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(local_path):
                    # 排除常见的不需要的目录
                    dirs[:] = [d for d in dirs if d not in {
                        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
                        '.idea', '.vscode', 'build', 'dist', '.next'
                    }]

                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(local_path)
                        zipf.write(file_path, arcname)

            # 上传到 claude-agent-sdk
            logger.info(f"正在上传到 claude-agent-sdk")
            claude_api_url = os.getenv("CLAUDE_CHAT_API_BASE_URL", "http://localhost:8003")

            with open(zip_path, 'rb') as f:
                files = {'file': (f'{repository.name}.zip', f, 'application/zip')}
                response = requests.post(
                    f"{claude_api_url}/session/create",
                    files=files,
                    timeout=60
                )

            if response.status_code != 201:
                error_detail = response.json().get('detail', 'Unknown error')
                raise HTTPException(
                    status_code=500,
                    detail=f"创建 Claude session 失败: {error_detail}"
                )

            # 获取 session_id
            result = response.json()
            session_id = result.get('session_id')

            # 更新数据库
            repository.claude_session_id = session_id
            db.commit()

            logger.info(f"Claude session 创建成功: {session_id}")

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Claude session 创建成功",
                    "session_id": session_id
                }
            )

        finally:
            # 清理临时文件
            if os.path.exists(zip_path):
                os.unlink(zip_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化 Claude session 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"初始化 Claude session 失败: {str(e)}"
        )


# 导出路由器
__all__ = ["repository_router", "analysis_router"]
