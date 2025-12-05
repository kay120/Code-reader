"""
依赖关系分析工具

分析代码文件之间的导入依赖关系，检测循环依赖
"""

import logging
import ast
import re
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """依赖关系分析器"""

    @staticmethod
    def extract_dependencies(code: str, language: str = "python") -> List[str]:
        """
        从代码中提取依赖关系

        Args:
            code: 代码内容
            language: 编程语言

        Returns:
            依赖模块列表
        """
        if language.lower() == "python":
            return DependencyAnalyzer._extract_python_dependencies(code)
        elif language.lower() in ["javascript", "typescript"]:
            return DependencyAnalyzer._extract_js_dependencies(code)
        else:
            return []

    @staticmethod
    def _extract_python_dependencies(code: str) -> List[str]:
        """提取 Python 代码的依赖"""
        dependencies = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # import xxx
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)

                # from xxx import yyy
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)

        except SyntaxError as e:
            logger.warning(f"Python 代码解析失败: {e}")
            # 回退到正则表达式
            return DependencyAnalyzer._extract_python_dependencies_regex(code)

        return list(set(dependencies))  # 去重

    @staticmethod
    def _extract_python_dependencies_regex(code: str) -> List[str]:
        """使用正则表达式提取 Python 依赖（回退方案）"""
        dependencies = []

        # 匹配 import xxx
        import_pattern = r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_\.]*)'
        # 匹配 from xxx import yyy
        from_pattern = r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s+import'

        for line in code.split('\n'):
            # import xxx
            match = re.match(import_pattern, line)
            if match:
                dependencies.append(match.group(1))
                continue

            # from xxx import yyy
            match = re.match(from_pattern, line)
            if match:
                dependencies.append(match.group(1))

        return list(set(dependencies))

    @staticmethod
    def _extract_js_dependencies(code: str) -> List[str]:
        """提取 JavaScript/TypeScript 代码的依赖"""
        dependencies = []

        # 匹配 import xxx from 'yyy'
        import_pattern = r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]"
        # 匹配 require('xxx')
        require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"

        for match in re.finditer(import_pattern, code):
            dependencies.append(match.group(1))

        for match in re.finditer(require_pattern, code):
            dependencies.append(match.group(1))

        return list(set(dependencies))

    @staticmethod
    def build_dependency_graph(
        file_dependencies: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        构建依赖关系图

        Args:
            file_dependencies: 文件依赖字典 {file_path: [dep1, dep2, ...]}

        Returns:
            依赖关系图数据
        """
        # 构建图
        graph = defaultdict(set)
        all_modules = set()

        for file_path, deps in file_dependencies.items():
            # 提取模块名
            module_name = DependencyAnalyzer._extract_module_name(file_path)
            all_modules.add(module_name)

            for dep in deps:
                # 只保留项目内部的依赖
                dep_module = DependencyAnalyzer._extract_module_name(dep)
                if dep_module in file_dependencies or dep in file_dependencies:
                    graph[module_name].add(dep_module)
                    all_modules.add(dep_module)

        # 转换为可序列化的格式
        graph_data = {
            "nodes": list(all_modules),
            "edges": [
                {"source": source, "target": target}
                for source, targets in graph.items()
                for target in targets
            ]
        }

        return graph_data

    @staticmethod
    def detect_circular_dependencies(
        file_dependencies: Dict[str, List[str]]
    ) -> List[List[str]]:
        """
        检测循环依赖

        Args:
            file_dependencies: 文件依赖字典

        Returns:
            循环依赖列表，每个元素是一个循环路径
        """
        # 构建图
        graph = defaultdict(set)

        for file_path, deps in file_dependencies.items():
            module_name = DependencyAnalyzer._extract_module_name(file_path)
            for dep in deps:
                dep_module = DependencyAnalyzer._extract_module_name(dep)
                if dep_module in file_dependencies or dep in file_dependencies:
                    graph[module_name].add(dep_module)

        # 使用 DFS 检测循环
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)

            rec_stack.remove(node)

        for node in graph.keys():
            if node not in visited:
                dfs(node, [])

        return cycles

    @staticmethod
    def _extract_module_name(file_path: str) -> str:
        """从文件路径提取模块名"""
        import os

        # 移除文件扩展名
        base_name = os.path.basename(file_path)
        module_name = os.path.splitext(base_name)[0]

        return module_name

    @staticmethod
    def analyze_dependencies_summary(
        file_dependencies: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        分析依赖关系摘要

        Args:
            file_dependencies: 文件依赖字典

        Returns:
            依赖关系摘要
        """
        # 统计
        total_files = len(file_dependencies)
        total_dependencies = sum(len(deps) for deps in file_dependencies.values())

        # 找出最多依赖的文件
        most_dependencies = []
        if file_dependencies:
            max_deps = max(len(deps) for deps in file_dependencies.values())
            most_dependencies = [
                {"file": file, "count": len(deps)}
                for file, deps in file_dependencies.items()
                if len(deps) == max_deps
            ]

        # 找出被依赖最多的模块
        dependency_count = defaultdict(int)
        for deps in file_dependencies.values():
            for dep in deps:
                dependency_count[dep] += 1

        most_depended = []
        if dependency_count:
            max_count = max(dependency_count.values())
            most_depended = [
                {"module": module, "count": count}
                for module, count in dependency_count.items()
                if count == max_count
            ]

        # 检测循环依赖
        circular_deps = DependencyAnalyzer.detect_circular_dependencies(file_dependencies)

        # 构建依赖图
        dependency_graph = DependencyAnalyzer.build_dependency_graph(file_dependencies)

        return {
            "total_files": total_files,
            "total_dependencies": total_dependencies,
            "average_dependencies": round(total_dependencies / total_files, 2) if total_files > 0 else 0,
            "most_dependencies": most_dependencies[:5],
            "most_depended": most_depended[:5],
            "circular_dependencies": circular_deps,
            "has_circular_dependencies": len(circular_deps) > 0,
            "dependency_graph": dependency_graph
        }

