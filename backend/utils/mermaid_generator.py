"""
Mermaid 图表生成工具

基于代码分析结果自动生成 Mermaid 格式的类图、调用图和依赖图
"""

import logging
from typing import List, Dict, Any, Set
import re

logger = logging.getLogger(__name__)


class MermaidGenerator:
    """Mermaid 图表生成器"""

    @staticmethod
    def generate_class_diagram(analysis_items: List[Dict[str, Any]]) -> str:
        """
        生成类图（Class Diagram）

        Args:
            analysis_items: 分析项列表，包含类和函数信息

        Returns:
            Mermaid 格式的类图代码
        """
        if not analysis_items:
            return ""

        mermaid_lines = ["classDiagram"]

        # 按类型分组
        classes = {}
        for item in analysis_items:
            target_type = item.get("target_type", "")
            target_name = item.get("target_name", "")
            description = item.get("description", "")

            if target_type == "class" and target_name:
                # 提取类的方法
                methods = MermaidGenerator._extract_methods_from_description(description)
                classes[target_name] = methods

        # 生成类定义
        for class_name, methods in classes.items():
            # 清理类名（移除特殊字符）
            clean_class_name = MermaidGenerator._sanitize_name(class_name)
            mermaid_lines.append(f"    class {clean_class_name} {{")

            # 添加方法
            for method in methods[:10]:  # 限制最多显示 10 个方法
                clean_method = MermaidGenerator._sanitize_name(method)
                mermaid_lines.append(f"        +{clean_method}()")

            mermaid_lines.append("    }")

        # 如果没有类，返回空字符串
        if len(mermaid_lines) == 1:
            return ""

        return "\n".join(mermaid_lines)

    @staticmethod
    def generate_dependency_graph(file_analyses: List[Dict[str, Any]]) -> str:
        """
        生成依赖关系图（Dependency Graph）

        Args:
            file_analyses: 文件分析结果列表

        Returns:
            Mermaid 格式的依赖图代码
        """
        if not file_analyses:
            return ""

        mermaid_lines = ["graph TD"]

        # 收集所有模块和依赖关系
        modules = set()
        dependencies = []

        for file_analysis in file_analyses:
            file_path = file_analysis.get("file_path", "")
            if not file_path:
                continue

            # 提取模块名（文件名）
            module_name = MermaidGenerator._extract_module_name(file_path)
            modules.add(module_name)

            # 提取依赖关系
            deps = file_analysis.get("dependencies", [])
            for dep in deps:
                dep_name = MermaidGenerator._extract_module_name(dep)
                if dep_name and dep_name != module_name:
                    dependencies.append((module_name, dep_name))

        # 生成节点定义
        for module in sorted(modules)[:20]:  # 限制最多显示 20 个模块
            clean_module = MermaidGenerator._sanitize_name(module)
            mermaid_lines.append(f"    {clean_module}[{module}]")

        # 生成依赖关系
        for source, target in dependencies[:30]:  # 限制最多显示 30 条依赖
            clean_source = MermaidGenerator._sanitize_name(source)
            clean_target = MermaidGenerator._sanitize_name(target)
            mermaid_lines.append(f"    {clean_source} --> {clean_target}")

        # 如果没有依赖关系，返回空字符串
        if len(mermaid_lines) == 1:
            return ""

        return "\n".join(mermaid_lines)

    @staticmethod
    def generate_flowchart(analysis_items: List[Dict[str, Any]], max_nodes: int = 15) -> str:
        """
        生成流程图（Flowchart）- 基于函数调用关系

        Args:
            analysis_items: 分析项列表
            max_nodes: 最大节点数

        Returns:
            Mermaid 格式的流程图代码
        """
        if not analysis_items:
            return ""

        mermaid_lines = ["flowchart TD"]

        # 提取函数和入口点
        functions = []
        entry_points = []

        for item in analysis_items:
            target_type = item.get("target_type", "")
            target_name = item.get("target_name", "")
            description = item.get("description", "")

            if target_type == "function" and target_name:
                functions.append({"name": target_name, "description": description})

                # 识别入口点（main, run, start, execute 等）
                if any(keyword in target_name.lower() for keyword in ["main", "run", "start", "execute", "init"]):
                    entry_points.append(target_name)

        # 如果没有函数，返回空字符串
        if not functions:
            return ""

        # 生成节点（限制数量）
        for func in functions[:max_nodes]:
            func_name = func["name"]
            clean_name = MermaidGenerator._sanitize_name(func_name)
            # 简化描述
            desc = func["description"][:30] + "..." if len(func["description"]) > 30 else func["description"]
            mermaid_lines.append(f'    {clean_name}["{func_name}"]')

        return "\n".join(mermaid_lines)

    @staticmethod
    def _extract_methods_from_description(description: str) -> List[str]:
        """从描述中提取方法名"""
        methods = []
        # 匹配常见的方法描述模式
        patterns = [
            r"方法[：:]\s*([a-zA-Z_][a-zA-Z0-9_]*)",
            r"函数[：:]\s*([a-zA-Z_][a-zA-Z0-9_]*)",
            r"`([a-zA-Z_][a-zA-Z0-9_]*)\(\)`",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, description)
            methods.extend(matches)

        return list(set(methods))  # 去重

    @staticmethod
    def _extract_module_name(file_path: str) -> str:
        """从文件路径提取模块名"""
        if not file_path:
            return ""

        # 移除文件扩展名
        import os
        base_name = os.path.basename(file_path)
        module_name = os.path.splitext(base_name)[0]

        return module_name

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """清理名称，移除 Mermaid 不支持的字符"""
        if not name:
            return "Unknown"

        # 移除特殊字符，只保留字母、数字和下划线
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # 确保以字母开头
        if sanitized and not sanitized[0].isalpha():
            sanitized = "M_" + sanitized

        return sanitized or "Unknown"

    @staticmethod
    def generate_all_diagrams(
        analysis_items: List[Dict[str, Any]], file_analyses: List[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        生成所有类型的图表

        Args:
            analysis_items: 分析项列表
            file_analyses: 文件分析结果列表（可选）

        Returns:
            包含所有图表的字典 {"class_diagram": "...", "dependency_graph": "...", "flowchart": "..."}
        """
        diagrams = {}

        # 生成类图
        class_diagram = MermaidGenerator.generate_class_diagram(analysis_items)
        if class_diagram:
            diagrams["class_diagram"] = class_diagram

        # 生成依赖图
        if file_analyses:
            dependency_graph = MermaidGenerator.generate_dependency_graph(file_analyses)
            if dependency_graph:
                diagrams["dependency_graph"] = dependency_graph

        # 生成流程图
        flowchart = MermaidGenerator.generate_flowchart(analysis_items)
        if flowchart:
            diagrams["flowchart"] = flowchart

        return diagrams

