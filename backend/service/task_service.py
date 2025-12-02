import asyncio
import logging
import os
import re
import traceback
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime
import httpx

from database import SessionLocal
from models import AnalysisTask

logger = logging.getLogger(__name__)

# 支持的代码文件扩展名
SUPPORTED_CODE_EXTENSIONS = {
    # 主流编程语言
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp",
    ".cs", ".go", ".rs", ".php", ".rb", ".swift", ".kt", ".scala", ".r",
    ".m", ".mm", ".pl", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
    
    # 配置和标记语言
    ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".properties", ".env", ".dockerfile",
    
    # 文档
    ".md", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc",
    
    # Web相关
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte",
    
    # 数据库
    ".sql", ".graphql", ".gql",
    
    # 其他
    ".ipynb", ".proto", ".thrift", ".avro",
}


# 辅助函数：根据文件扩展名获取编程语言
def get_language_from_extension(file_path: str) -> str:
    """根据文件扩展名获取编程语言类型"""
    extension = file_path.split(".")[-1].lower() if "." in file_path else ""
    
    language_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "jsx": "javascript",
        "java": "java",
        "cpp": "cpp",
        "c": "c",
        "cs": "csharp",
        "php": "php",
        "rb": "ruby",
        "go": "go",
        "rs": "rust",
        "kt": "kotlin",
        "swift": "swift",
        "md": "markdown",
        "txt": "text",
        "json": "json",
        "xml": "xml",
        "html": "html",
        "css": "css",
        "scss": "scss",
        "sass": "sass",
        "yml": "yaml",
        "yaml": "yaml",
        "toml": "toml",
        "ini": "ini",
        "cfg": "config",
        "conf": "config",
        "sh": "shell",
        "bat": "batch",
        "ps1": "powershell",
        "sql": "sql",
        "r": "r",
        "scala": "scala",
        "clj": "clojure",
        "hs": "haskell",
        "elm": "elm",
        "dart": "dart",
        "vue": "vue",
        "svelte": "svelte",
    }

    return language_map.get(extension, "text")


# 辅助函数：判断是否应该跳过的文件类型
def should_skip_file(file_path: str) -> bool:
    """判断是否应该跳过该文件"""
    extension = file_path.split(".")[-1].lower() if "." in file_path else ""

    skip_extensions = {
        # 图片
        "jpg", "jpeg", "png", "gif", "bmp", "svg", "ico", "webp",
        # 压缩包
        "zip", "rar", "7z", "tar", "gz", "bz2", "xz",
        # 办公文档
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        # 媒体文件
        "mp3", "mp4", "avi", "mov", "wmv", "flv", "mkv",
        # 二进制文件
        "exe", "dll", "so", "dylib", "bin",
        # 字体文件
        "woff", "woff2", "ttf", "eot",
        # 临时文件
        "lock", "log", "tmp", "cache",
    }
    
    return extension in skip_extensions


# 辅助函数：计算代码行数
def count_code_lines(content: str) -> int:
    """计算代码行数（排除空行）"""
    return len([line for line in content.split("\n") if line.strip()])


# 辅助函数：生成基于文件类型的模拟内容
def generate_mock_file_content(file_path: str, language: str) -> str:
    """生成基于文件类型的模拟内容"""
    file_name = os.path.basename(file_path)
    class_name = re.sub(r"[^a-zA-Z0-9]", "", file_name.split(".")[0])

    if language == "python":
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{file_name} - Python模块
"""

import os
import sys
import re
from datetime import datetime
from typing import List, Dict, Optional

class {class_name}:
    """{file_name} 类"""

    def __init__(self):
        self.name = "{file_name}"
        self.created_at = datetime.now()

    def process(self, data: Dict) -> Optional[List]:
        """处理数据"""
        if not data:
            return None

        result = []
        for key, value in data.items():
            if isinstance(value, str):
                result.append(value.strip())

        return result

if __name__ == "__main__":
    instance = {class_name}()
    print(f"Running {{instance.name}}")'''

    elif language in ["javascript", "typescript"]:
        if language == "typescript":
            return f'''/**
 * {file_name} - TypeScript模块
 */

import {{ readFile, writeFile }} from 'fs/promises';
import {{ join }} from 'path';

interface DataItem {{
    id: string;
    name: string;
    value: any;
}}

interface ProcessResult {{
    success: boolean;
    data: DataItem[];
    timestamp: Date;
}}

export class {class_name} {{
    private readonly name: string;
    private readonly version: string;

    constructor() {{
        this.name = '{file_name}';
        this.version = '1.0.0';
    }}

    public async process(items: DataItem[]): Promise<ProcessResult> {{
        if (!items || items.length === 0) {{
            throw new Error('Items array is required');
        }}

        const processedData = items.map(item => ({{
            ...item,
            processed: true,
            timestamp: new Date()
        }}));

        return {{
            success: true,
            data: processedData,
            timestamp: new Date()
        }};
    }}

    public getName(): string {{
        return this.name;
    }}
}}

export default {class_name};'''
        else:  # javascript
            return f'''/**
 * {file_name} - JavaScript模块
 */

const fs = require('fs');
const path = require('path');
const util = require('util');

class {class_name} {{
    constructor() {{
        this.name = '{file_name}';
        this.version = '1.0.0';
    }}

    async process(data) {{
        if (!data) {{
            throw new Error('Data is required');
        }}

        const result = Object.keys(data).map(key => {{
            return {{
                key,
                value: data[key],
                processed: true
            }};
        }});

        return result;
    }}

    static getInstance() {{
        if (!this.instance) {{
            this.instance = new {class_name}();
        }}
        return this.instance;
    }}
}}

module.exports = {class_name};'''

    elif language == "markdown":
        return f'''# {file_name}

## 概述

这是 {file_name} 文档文件。

## 功能特性

- 功能1：数据处理
- 功能2：文件操作
- 功能3：配置管理

## 使用方法

```bash
# 安装依赖
npm install

# 运行项目
npm start
```

## API 文档

### 方法列表

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| process | data: Object | Promise<Array> | 处理数据 |
| validate | input: string | boolean | 验证输入 |

## 配置说明

配置文件位于 `config/` 目录下。

## 更新日志

- v1.0.0: 初始版本
- v1.1.0: 添加新功能
'''

    elif language == "json":
        return f'''{{
  "name": "{file_name.replace('.json', '')}",
  "version": "1.0.0",
  "description": "{file_name} 配置文件",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "test": "jest",
    "build": "webpack --mode production"
  }},
  "dependencies": {{
    "express": "^4.18.0",
    "lodash": "^4.17.21",
    "moment": "^2.29.0"
  }},
  "devDependencies": {{
    "jest": "^28.0.0",
    "webpack": "^5.70.0"
  }},
  "keywords": [
    "config",
    "settings", 
    "application"
  ],
  "author": "Developer",
  "license": "MIT"
}}'''

    else:  # default
        return f'''# {file_name}
# 这是 {file_name} 文件
# 文件类型: {language}

# 配置项
name = "{file_name}"
version = "1.0.0"
description = "{file_name} 配置文件"

# 基本设置
debug = true
port = 3000
host = "localhost"

# 数据库配置
database_url = "sqlite:///app.db"
max_connections = 10

# 日志配置
log_level = "info"
log_file = "app.log"
'''


# 辅助函数：提取依赖信息
def extract_dependencies(content: str, language: str) -> str:
    """提取依赖信息"""
    dependencies: Set[str] = set()
    
    if language == "python":
        # Python import 语句
        python_imports = re.findall(r'^(?:from\s+(\S+)\s+)?import\s+([^\n#]+)', content, re.MULTILINE)
        for from_part, import_part in python_imports:
            if from_part:
                dependencies.add(from_part.split('.')[0])
            else:
                # 处理 import 部分
                parts = re.split(r'[,\s]+', import_part.strip())
                for part in parts:
                    clean_part = part.strip().split('.')[0]
                    if clean_part and not clean_part.startswith('.'):
                        dependencies.add(clean_part)
                        
    elif language in ["javascript", "typescript"]:
        # JavaScript/TypeScript import/require 语句
        js_imports = re.findall(r'(?:import.*?from\s+[\'"`]([^\'"`]+)[\'"`]|require\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\))', content)
        for match in js_imports:
            module_name = match[0] or match[1]
            if module_name and not module_name.startswith('.'):
                dependencies.add(module_name.split('/')[0])
                
    elif language == "java":
        # Java import 语句
        java_imports = re.findall(r'^import\s+([^;]+);', content, re.MULTILINE)
        for imp in java_imports:
            package_parts = imp.strip().split('.')
            if len(package_parts) >= 2:
                dependencies.add(f"{package_parts[0]}.{package_parts[1]}")
                
    return "|".join(sorted(dependencies))


def get_file_list_from_path(local_path: str) -> List[str]:
    """从本地路径获取文件列表"""
    try:
        # 处理相对路径，转换为绝对路径
        if not os.path.isabs(local_path):
            # 获取项目根目录
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent  # 回到backend目录
            project_root = backend_dir.parent  # 回到项目根目录
            repo_path = project_root / local_path.lstrip('../').lstrip('..\\')
        else:
            repo_path = Path(local_path)
            
        if not repo_path.exists():
            logger.error(f"路径不存在: {local_path} -> {repo_path}")
            return []
        
        # 使用简化的文件扫描逻辑
        files = []
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                # 转换为相对路径字符串
                relative_path = str(file_path.relative_to(repo_path))
                files.append(relative_path)
        
        logger.info(f"从 {local_path} 扫描到 {len(files)} 个文件")
        return files
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        return []


async def execute_step_0_scan_files(task_id: int, local_path: str, db) -> Dict:
    """步骤0: 扫描代码文件"""
    # 延迟导入避免循环依赖
    from services import FileAnalysisService
    
    logger.info(f"开始执行步骤0: 扫描代码文件 - 任务ID: {task_id}")
    
    try:
        # 获取文件列表
        file_list = get_file_list_from_path(local_path)
        if not file_list:
            logger.warning(f"任务 {task_id} 没有找到文件")
            return {
                "success": True,
                "message": "没有找到文件",
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0,
                "total_code_lines": 0
            }
        
        # 统计信息
        total_code_lines = 0
        successful_files = 0
        failed_files = 0
        
        # 获取仓库根路径
        if not os.path.isabs(local_path):
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent
            project_root = backend_dir.parent
            repo_path = project_root / local_path.lstrip("../")
        else:
            repo_path = Path(local_path)

        # 对每个文件创建分析记录
        for file_path in file_list:
            try:
                # 跳过不需要分析的文件类型
                if should_skip_file(file_path):
                    logger.debug(f"跳过文件: {file_path} (不支持的文件类型)")
                    continue

                # 获取语言类型
                language = get_language_from_extension(file_path)

                # 读取实际文件内容
                full_file_path = repo_path / file_path
                real_file_content = ""
                try:
                    with open(full_file_path, "r", encoding="utf-8") as f:
                        real_file_content = f.read()
                except UnicodeDecodeError:
                    # 如果UTF-8解码失败，尝试其他编码
                    try:
                        with open(full_file_path, "r", encoding="gbk") as f:
                            real_file_content = f.read()
                    except Exception as decode_error:
                        logger.warning(f"无法读取文件 {file_path}: {decode_error}")
                        real_file_content = ""
                except Exception as read_error:
                    logger.warning(f"无法读取文件 {file_path}: {read_error}")
                    real_file_content = ""

                code_lines = count_code_lines(real_file_content)
                dependencies = extract_dependencies(real_file_content, language)

                # 创建文件分析数据
                file_analysis_data = {
                    "task_id": task_id,
                    "file_path": file_path,
                    "language": language,
                    "analysis_version": "1.0",
                    "status": "pending",
                    "code_lines": code_lines,
                    "code_content": real_file_content,
                    "file_analysis": "",
                    "dependencies": dependencies,
                    "error_message": "",
                }

                # 调用服务创建文件分析记录
                result = FileAnalysisService.create_file_analysis(file_analysis_data, db)

                if result["status"] == "success":
                    logger.debug(f"文件 {file_path} 分析记录创建成功")
                    successful_files += 1
                    total_code_lines += code_lines
                else:
                    logger.error(f"文件 {file_path} 分析记录创建失败: {result['message']}")
                    failed_files += 1

            except Exception as file_error:
                logger.error(f"处理文件 {file_path} 时出错: {str(file_error)}")
                failed_files += 1
                continue

        logger.info(f"步骤0完成 - 成功: {successful_files}, 失败: {failed_files}, 总代码行数: {total_code_lines}")

        return {
            "success": True,
            "message": "扫描代码文件完成",
            "total_files": len(file_list),
            "successful_files": successful_files,
            "failed_files": failed_files,
            "total_code_lines": total_code_lines,
        }

    except Exception as e:
        logger.error(f"步骤0执行失败: {str(e)}")
        return {
            "success": False,
            "message": f"步骤0执行失败: {str(e)}",
            "total_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "total_code_lines": 0,
        }


async def execute_step_1_create_knowledge_base(task_id: int, local_path: str, repo_info: Dict) -> Dict:
    """步骤1: 知识库创建"""
    logger.info(f"开始执行步骤1: 知识库创建 - 任务ID: {task_id}")

    try:
        # 添加项目根目录到Python路径
        import sys
        from pathlib import Path

        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent
        project_root = backend_dir.parent

        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        # 动态导入知识库创建flow
        logger.info(f"调用知识库创建flow - 本地路径: {local_path}")
        from src.flows.web_flow import create_knowledge_base as create_kb_flow

        # 执行知识库创建flow
        result = await create_kb_flow(task_id=task_id, local_path=local_path, repo_info=repo_info)

        # 检查flow执行结果
        if result.get("status") == "knowledge_base_ready" and result.get("vectorstore_index"):
            logger.info(f"知识库创建成功，索引: {result.get('vectorstore_index')}")
            return {"success": True, "message": "知识库创建完成", "vectorstore_index": result.get("vectorstore_index")}
        else:
            logger.error(f"知识库创建失败: {result}")
            return {"success": False, "message": f"知识库创建失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        logger.error(f"步骤1执行失败: {str(e)}")
        return {"success": False, "message": f"步骤1执行失败: {str(e)}"}


async def execute_step_2_analyze_data_model(task_id: int, vectorstore_index: str) -> Dict:
    """步骤2: 分析数据模型"""
    logger.info(f"开始执行步骤2: 分析数据模型 - 任务ID: {task_id}")

    try:
        # 添加项目根目录到Python路径
        import sys
        from pathlib import Path

        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent
        project_root = backend_dir.parent
        src_path = project_root / "src"

        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        # 动态导入分析数据模型flow
        try:
            from src.flows.web_flow import analyze_data_model as analyze_dm_flow
        except ImportError as import_error:
            logger.error(f"无法导入分析数据模型flow: {import_error}")
            return {"success": False, "message": f"无法导入分析数据模型flow: {import_error}"}

        logger.info(f"调用分析数据模型flow - 向量索引: {vectorstore_index}")

        # 执行分析数据模型flow（异步模式：只提交任务，不等待完成）
        result = await analyze_dm_flow(task_id=task_id, vectorstore_index=vectorstore_index)

        # 检查flow执行结果
        if result.get("status") == "analysis_submitted":
            # 异步模式：任务已提交到队列
            total_files = result.get("total_files", 0)
            submitted_files = result.get("submitted_files", 0)
            failed_submissions = result.get("failed_submissions", 0)
            success_rate = result.get("success_rate", "0%")

            logger.info(
                f"✅ 分析任务已提交: 总文件 {total_files}, 成功提交 {submitted_files}, 提交失败 {failed_submissions}"
            )
            logger.info(f"💡 任务将在后台异步执行，不阻塞主流程")

            return {
                "success": True,
                "message": result.get("message", "分析任务已提交到后台队列"),
                "total_files": total_files,
                "submitted_files": submitted_files,
                "failed_submissions": failed_submissions,
                "success_rate": success_rate,
            }
        elif result.get("status") == "analysis_completed":
            # 兼容旧版本：同步模式
            analysis_items_count = result.get("analysis_items_count", 0)
            total_files = result.get("total_files", 0)
            successful_files = result.get("successful_files", 0)
            failed_files = result.get("failed_files", 0)
            success_rate = result.get("success_rate", "0%")

            logger.info(
                f"分析数据模型完成: 总文件 {total_files}, 成功 {successful_files}, 失败 {failed_files}, 分析项 {analysis_items_count}"
            )

            return {
                "success": True,
                "message": result.get("message", "分析数据模型完成"),
                "analysis_items_count": analysis_items_count,
                "total_files": total_files,
                "successful_files": successful_files,
                "failed_files": failed_files,
                "success_rate": success_rate,
            }
        else:
            logger.error(f"分析数据模型失败: {result}")
            return {"success": False, "message": f"分析数据模型失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        logger.error(f"步骤2执行失败: {str(e)}")
        return {"success": False, "message": f"步骤2执行失败: {str(e)}"}


async def execute_step_3_generate_document_structure(task_id: int, external_file_path: str, repo_info: Dict = None) -> Dict:
    """步骤3: 生成文档结构"""
    # 延迟导入避免循环依赖
    from services import TaskReadmeService

    logger.info(f"开始执行步骤3: 生成文档结构 - 任务ID: {task_id}")

    try:
        # 检查external_file_path是否已经是deepwiki的上传路径
        # 如果是本地路径,需要先上传到deepwiki
        deepwiki_path = external_file_path

        # 判断是否需要上传: 如果路径包含本地目录标识,则需要上传
        needs_upload = (
            external_file_path.startswith("data/repos/") or
            external_file_path.startswith("./data/repos/") or
            "/data/repos/" in external_file_path
        )

        if needs_upload:
            logger.info(f"检测到本地路径,需要上传到deepwiki: {external_file_path}")

            # 将本地路径转换为绝对路径
            from pathlib import Path
            if not os.path.isabs(external_file_path):
                current_file = Path(__file__).resolve()
                backend_dir = current_file.parent.parent
                local_path = (backend_dir / external_file_path).resolve()
            else:
                local_path = Path(external_file_path)

            logger.info(f"本地绝对路径: {local_path}")

            # 打包成zip并上传到deepwiki
            import tempfile
            import zipfile
            import requests

            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
                zip_path = tmp_zip.name

                # 创建zip文件
                logger.info(f"正在打包代码仓库: {local_path}")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(local_path):
                        # 跳过隐藏目录和常见的忽略目录
                        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.venv']]

                        for file in files:
                            if file.startswith('.'):
                                continue
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, local_path)
                            zipf.write(file_path, arcname)

                logger.info(f"代码仓库打包完成: {zip_path}")

                # 上传到deepwiki
                readme_api_base_url = os.getenv("README_API_BASE_URL", "http://localhost:8001")
                upload_url = f"{readme_api_base_url}/api/upload/zip"

                logger.info(f"正在上传到deepwiki: {upload_url}")

                try:
                    with open(zip_path, 'rb') as f:
                        files = {'file': (f'{local_path.name}.zip', f, 'application/x-zip-compressed')}
                        headers = {'accept': 'application/json'}
                        response = requests.post(upload_url, files=files, headers=headers, timeout=60)

                        if response.status_code == 200:
                            upload_result = response.json()
                            if upload_result.get("success"):
                                deepwiki_path = upload_result.get("file_path")
                                logger.info(f"上传成功,deepwiki路径: {deepwiki_path}")
                            else:
                                error_msg = upload_result.get('message', '未知错误')
                                logger.error(f"上传失败: {error_msg}")
                                return {"success": False, "message": f"上传到deepwiki失败: {error_msg}"}
                        else:
                            logger.error(f"上传请求失败,状态码: {response.status_code}")
                            return {"success": False, "message": f"上传到deepwiki失败,状态码: {response.status_code}"}
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(zip_path)
                    except:
                        pass
        else:
            logger.info(f"使用已有的deepwiki路径: {deepwiki_path}")

        # 1. 调用外部README API生成文档结构
        logger.info("调用外部README API生成文档结构...")

        logger.info(f"传递给README API的路径: {deepwiki_path}")

        # 从环境变量或配置中获取README API基础URL和模型配置
        readme_api_base_url = os.getenv("README_API_BASE_URL", "http://localhost:80111")
        openai_model = os.getenv("OPENAI_MODEL", "kimi-k2-0905-preview")

        # 提取项目名称
        project_name = None
        if repo_info:
            project_name = repo_info.get("name") or repo_info.get("full_name")
            if project_name and "/" in project_name:
                # 从 "owner/repo" 中提取 "repo"
                project_name = project_name.split("/")[-1]

        request_data = {
            "local_path": deepwiki_path,  # 使用转换后的deepwiki路径
            "project_name": project_name,  # 传递真实项目名称
            "generate_readme": True,
            "analyze_dependencies": True,
            "generate_architecture_diagram": True,
            "language": "zh",
            "provider": "openai",
            "model": openai_model,  # 从环境变量读取
            "export_format": "markdown",
            "analysis_depth": "detailed",
            "include_code_examples": True,
        }
        print(request_data)

        max_create_attempts = 50
        retry_delay_seconds = 5
        request_timeout = httpx.Timeout(600.0)
        readme_api_task_id = None

        async with httpx.AsyncClient(timeout=request_timeout) as client:
            for attempt in range(1, max_create_attempts + 1):
                try:
                    response = await client.post(f"{readme_api_base_url}/api/analyze/local", json=request_data)
                except httpx.RequestError as exc:
                    logger.warning(f"文档结构生成任务创建请求失败(第 {attempt}/{max_create_attempts} 次尝试): {exc}")
                    if attempt < max_create_attempts:
                        await asyncio.sleep(retry_delay_seconds)
                    continue

                if response.status_code == 200:
                    result = response.json()
                    print(result)
                    readme_api_task_id = result.get("task_id")
                    logger.info(f"文档结构生成任务已创建，任务ID: {readme_api_task_id}")
                    break

                error_data = (
                    response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                )
                logger.error(f"文档结构生成任务创建失败(第 {attempt}/{max_create_attempts} 次尝试): {error_data}")
                if attempt < max_create_attempts:
                    logger.info(f"将在 {retry_delay_seconds} 秒后重试创建文档结构任务")
                    await asyncio.sleep(retry_delay_seconds)
                else:
                    return {
                        "success": False,
                        "message": f"文档结构生成任务创建失败: {error_data.get('message', response.text)}",
                    }

        if not readme_api_task_id:
            return {"success": False, "message": "文档结构生成任务创建失败: 请求在最大重试次数后仍未成功"}

        # 2. 轮询检查生成状态
        logger.info("开始轮询检查文档生成状态...")
        completed = False
        attempts = 0
        max_attempts = 60  # 最多轮询60次（5分钟）
        poll_interval = 5  # 每5秒检查一次

        while not completed and attempts < max_attempts:
            attempts += 1
            logger.info(f"第 {attempts} 次检查文档生成状态...")

            try:
                # 增加超时时间到60秒，并添加重试逻辑
                async with httpx.AsyncClient(timeout=60.0) as client:
                    status_response = await client.get(
                        f"{readme_api_base_url}/api/analyze/local/{readme_api_task_id}/status"
                    )

                    if status_response.status_code == 200:
                        status_result = status_response.json()

                        if status_result.get("status") == "completed":
                            logger.info("文档结构生成完成!")

                            # 3. 获取生成的文档内容
                            if status_result.get("result") and status_result["result"].get("markdown"):
                                markdown_content = status_result["result"]["markdown"]
                                logger.info(f"获取到生成的文档内容，长度: {len(markdown_content)}")

                                # 4. 保存到本项目数据库
                                logger.info("保存文档到数据库...")
                                readme_data = {"task_id": task_id, "content": markdown_content}

                                # 使用数据库会话来保存文档

                                with SessionLocal() as db:
                                    save_result = TaskReadmeService.create_task_readme(readme_data, db)

                                    if save_result["status"] == "success":
                                        logger.info("文档结构生成并保存成功")
                                        completed = True
                                        return {
                                            "success": True,
                                            "message": "文档结构生成并保存成功",
                                            "content_length": len(markdown_content),
                                        }
                                    else:
                                        logger.error(f"保存文档到数据库失败: {save_result['message']}")
                                        return {
                                            "success": False,
                                            "message": f"保存文档到数据库失败: {save_result['message']}",
                                        }
                            else:
                                logger.error("生成的文档内容为空")
                                return {"success": False, "message": "生成的文档内容为空"}

                        elif status_result.get("status") == "failed" or status_result.get("error"):
                            logger.error(f"文档生成失败: {status_result.get('error', status_result.get('message'))}")
                            return {
                                "success": False,
                                "message": f"文档生成失败: {status_result.get('error', status_result.get('message'))}",
                            }
                        else:
                            # 仍在进行中，显示进度
                            progress = status_result.get("progress", 0)
                            current_stage = status_result.get("current_stage", "处理中")
                            logger.info(f"文档生成进度: {progress}% - {current_stage}")

                            # 等待下次检查
                            await asyncio.sleep(poll_interval)
                    else:
                        logger.error(f"检查文档生成状态失败: HTTP {status_response.status_code}")
                        await asyncio.sleep(poll_interval)

            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as timeout_error:
                logger.warning(f"第 {attempts} 次状态检查超时: {str(timeout_error)}")
                print(f"状态检查超时 (第{attempts}次): {str(timeout_error)}")

                # 如果还有重试机会，继续等待后重试
                if attempts < max_attempts:
                    logger.info(f"等待 {poll_interval} 秒后重试...")
                    await asyncio.sleep(poll_interval)
                else:
                    logger.error("已达到最大重试次数，状态检查失败")

            except httpx.RequestError as req_error:
                logger.error(f"第 {attempts} 次状态检查请求错误: {str(req_error)}")
                print(f"状态检查请求错误 (第{attempts}次): {str(req_error)}")

                # 网络错误也继续重试
                if attempts < max_attempts:
                    logger.info(f"等待 {poll_interval} 秒后重试...")
                    await asyncio.sleep(poll_interval)
                else:
                    logger.error("已达到最大重试次数，状态检查失败")

            except Exception as unexpected_error:
                logger.error(f"状态检查发生意外错误: {str(unexpected_error)}")
                print(f"状态检查意外错误: {str(unexpected_error)}")
                # 意外错误也重试
                await asyncio.sleep(poll_interval)

        if not completed:
            logger.error("文档生成超时")
            return {"success": False, "message": "文档生成超时"}

    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"步骤3执行失败: {str(e)}")
        logger.error(f"步骤3异常详细信息:\n{error_traceback}")
        print(f"=== 步骤3异常详细信息 ===\n{error_traceback}")
        return {"success": False, "message": f"步骤3执行失败: {str(e)}"}


async def run_task(task_id: int, external_file_path: str):
    """运行分析任务的主函数"""
    # 延迟导入避免循环依赖
    from services import AnalysisTaskService, RepositoryService
    from database import get_db_async

    logger.info(f"开始运行任务 {task_id}")

    async with get_db_async() as db:
        try:
            # 获取任务信息
            task_result = AnalysisTaskService.get_task_by_id(task_id, db)
            if task_result["status"] != "success":
                logger.error(f"获取任务失败: {task_result['message']}")
                return {"status": "error", "message": task_result["message"]}

            task_data = task_result["task"]
            repository_id = task_data["repository_id"]

            # 获取仓库信息
            repo_result = RepositoryService.get_repository_by_id(repository_id, db)
            if repo_result["status"] != "success":
                logger.error(f"获取仓库失败: {repo_result['message']}")
                return {"status": "error", "message": repo_result["message"]}

            repository = repo_result["repository"]
            local_path = repository.get("local_path")

            if not local_path:
                logger.error(f"仓库 {repository_id} 没有本地路径")
                return {"status": "error", "message": "仓库缺少本地路径"}

            # 更新任务状态为运行中
            task_obj = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if task_obj:
                task_obj.status = "running"
                if not task_obj.start_time:  # 只在第一次运行时设置开始时间
                    task_obj.start_time = datetime.now()
                db.commit()

            logger.info(f"任务 {task_id} 使用仓库路径: {local_path}")

            # 准备仓库信息
            repo_info = {
                "full_name": repository.get("full_name") or repository.get("name"),
                "name": repository.get("name"),
                "local_path": local_path,
            }

            # ========== 检查是否是恢复任务 ==========
            is_resume = False
            vectorstore_index = None

            if task_obj and task_obj.task_index:
                # 如果已有 task_index，说明步骤0和步骤1已完成
                is_resume = True
                vectorstore_index = task_obj.task_index
                logger.info(f"🔄 检测到恢复任务，跳过步骤0和步骤1，使用已有索引: {vectorstore_index}")
                logger.info(f"📊 当前进度: {task_obj.successful_files}/{task_obj.total_files} 个文件已完成")

            # ========== 执行4个分析步骤 ==========

            if not is_resume:
                # 步骤0: 扫描代码文件
                logger.info("=== 开始执行步骤0: 扫描代码文件 ===")
                step0_result = await execute_step_0_scan_files(task_id, local_path, db)

                if not step0_result["success"]:
                    logger.error(f"步骤0失败: {step0_result['message']}")
                    # 更新任务状态为失败
                    if task_obj:
                        task_obj.status = "failed"
                        task_obj.end_time = datetime.now()
                        db.commit()
                    return {"status": "error", "message": f"步骤0失败: {step0_result['message']}"}

                # 更新任务统计信息
                if task_obj:
                    task_obj.total_files = step0_result.get("total_files", 0)
                    # 注意：步骤 0 只是扫描文件，不更新 successful_files
                    # successful_files 应该在文件实际分析完成时更新
                    task_obj.successful_files = 0  # 初始化为 0
                    task_obj.failed_files = 0  # 初始化为 0
                    task_obj.code_lines = step0_result.get("total_code_lines", 0)
                    db.commit()

                logger.info(f"步骤0完成: {step0_result['message']}")

                # 步骤1: 知识库创建
                logger.info("=== 开始执行步骤1: 知识库创建 ===")
                step1_result = await execute_step_1_create_knowledge_base(task_id, local_path, repo_info)

                if not step1_result["success"]:
                    logger.error(f"步骤1失败: {step1_result['message']}")
                    if task_obj:
                        task_obj.status = "failed"
                        task_obj.end_time = datetime.now()
                        db.commit()
                    return {"status": "error", "message": f"步骤1失败: {step1_result['message']}"}

                vectorstore_index = step1_result.get("vectorstore_index")

                # 更新任务索引
                if task_obj and vectorstore_index:
                    task_obj.task_index = vectorstore_index
                    db.commit()

                logger.info(f"步骤1完成: {step1_result['message']}")
            else:
                # 恢复任务，使用已有的统计信息
                step0_result = {
                    "success": True,
                    "message": "跳过步骤0（恢复任务）",
                    "total_files": task_obj.total_files,
                    "total_code_lines": task_obj.code_lines,
                }
                step1_result = {
                    "success": True,
                    "message": "跳过步骤1（恢复任务）",
                    "vectorstore_index": vectorstore_index,
                }

            # 步骤2: 分析数据模型
            logger.info("=== 开始执行步骤2: 分析数据模型 ===")

            if not vectorstore_index:
                logger.error("缺少向量索引，无法执行数据模型分析")
                if task_obj:
                    task_obj.status = "failed"
                    task_obj.end_time = datetime.now()
                    db.commit()
                return {"status": "error", "message": "缺少向量索引，无法执行数据模型分析"}

            step2_result = await execute_step_2_analyze_data_model(task_id, vectorstore_index)

            if not step2_result["success"]:
                logger.error(f"步骤2失败: {step2_result['message']}")
                if task_obj:
                    task_obj.status = "failed"
                    task_obj.end_time = datetime.now()
                    db.commit()
                return {"status": "error", "message": f"步骤2失败: {step2_result['message']}"}

            logger.info(f"步骤2完成: {step2_result['message']}")

            # ========== 异步模式：步骤 2 完成后立即结束，释放 Worker ==========
            # 步骤 3 将在所有文件分析完成后自动触发

            # 更新任务状态为 processing（表示正在后台处理）
            if task_obj:
                task_obj.status = "processing"  # 改为 processing，表示文件分析正在后台执行
                task_obj.progress_percentage = 50  # 步骤 0-1 完成，步骤 2 已提交
                db.commit()

            logger.info(f"✅ 任务 {task_id} 步骤 0-2 完成，文件分析任务已提交到后台队列")
            logger.info(f"💡 步骤 3（生成文档）将在所有文件分析完成后自动触发")

            return {
                "status": "success",
                "message": "任务已提交到后台队列，正在异步执行",
                "task_id": task_id,
                "step0_result": step0_result,
                "step1_result": step1_result,
                "step2_result": step2_result,
            }

        except Exception as e:
            logger.error(f"运行任务 {task_id} 时发生错误: {str(e)}")

            # 更新任务状态为失败
            try:
                task_obj = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                if task_obj:
                    task_obj.status = "failed"
                    task_obj.end_time = datetime.now()
                    task_obj.current_file = None  # 清空当前处理文件
                    db.commit()
            except Exception as update_error:
                logger.error(f"更新任务状态失败: {str(update_error)}")

            return {"status": "error", "message": f"任务执行失败: {str(e)}"}
