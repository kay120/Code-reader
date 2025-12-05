"""
代码质量分析工具

使用 radon 库分析代码复杂度、可维护性等指标
"""

import logging
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)


class CodeQualityAnalyzer:
    """代码质量分析器"""

    @staticmethod
    def analyze_code_quality(code: str, language: str = "python") -> Dict[str, Any]:
        """
        分析代码质量

        Args:
            code: 代码内容
            language: 编程语言

        Returns:
            质量分析结果字典
        """
        if language.lower() != "python":
            # 目前只支持 Python
            return {
                "language": language,
                "supported": False,
                "message": f"暂不支持 {language} 语言的质量分析"
            }

        try:
            # 分析各项指标
            complexity = CodeQualityAnalyzer._analyze_complexity(code)
            maintainability = CodeQualityAnalyzer._analyze_maintainability(code)
            comment_ratio = CodeQualityAnalyzer._calculate_comment_ratio(code)
            code_metrics = CodeQualityAnalyzer._calculate_code_metrics(code)

            # 计算综合评分
            quality_score = CodeQualityAnalyzer._calculate_quality_score(
                complexity, maintainability, comment_ratio, code_metrics
            )

            return {
                "language": language,
                "supported": True,
                "complexity": complexity,
                "maintainability": maintainability,
                "comment_ratio": comment_ratio,
                "code_metrics": code_metrics,
                "quality_score": quality_score,
                "grade": CodeQualityAnalyzer._get_quality_grade(quality_score)
            }

        except Exception as e:
            logger.error(f"代码质量分析失败: {e}", exc_info=True)
            return {
                "language": language,
                "supported": True,
                "error": str(e)
            }

    @staticmethod
    def _analyze_complexity(code: str) -> Dict[str, Any]:
        """分析代码复杂度（圈复杂度）"""
        try:
            from radon.complexity import cc_visit, average_complexity

            # 计算圈复杂度
            complexity_results = cc_visit(code)

            if not complexity_results:
                return {
                    "average": 1.0,
                    "max": 1,
                    "total": 0,
                    "functions": []
                }

            # 提取函数复杂度
            functions = []
            for result in complexity_results:
                functions.append({
                    "name": result.name,
                    "complexity": result.complexity,
                    "rank": result.rank  # A, B, C, D, E, F
                })

            # 计算平均复杂度
            avg_complexity = average_complexity(complexity_results)

            # 找出最大复杂度
            max_complexity = max([r.complexity for r in complexity_results])

            return {
                "average": round(avg_complexity, 2),
                "max": max_complexity,
                "total": len(complexity_results),
                "functions": functions[:10]  # 只返回前 10 个
            }

        except Exception as e:
            logger.warning(f"复杂度分析失败: {e}")
            return {
                "average": 0,
                "max": 0,
                "total": 0,
                "error": str(e)
            }

    @staticmethod
    def _analyze_maintainability(code: str) -> Dict[str, Any]:
        """分析可维护性指数（Maintainability Index）"""
        try:
            from radon.metrics import mi_visit, mi_rank

            # 计算可维护性指数
            mi_score = mi_visit(code, multi=True)

            if not mi_score:
                return {
                    "score": 100,
                    "rank": "A"
                }

            # mi_score 是 0-100 的分数，越高越好
            # A: 20-100, B: 10-19, C: 0-9
            rank = mi_rank(mi_score)

            return {
                "score": round(mi_score, 2),
                "rank": rank
            }

        except Exception as e:
            logger.warning(f"可维护性分析失败: {e}")
            return {
                "score": 0,
                "error": str(e)
            }

    @staticmethod
    def _calculate_comment_ratio(code: str) -> Dict[str, Any]:
        """计算注释覆盖率"""
        try:
            lines = code.split('\n')
            total_lines = len(lines)
            comment_lines = 0
            code_lines = 0

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith('#'):
                    comment_lines += 1
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    comment_lines += 1
                else:
                    code_lines += 1

            # 计算注释率
            if code_lines == 0:
                ratio = 0
            else:
                ratio = (comment_lines / (comment_lines + code_lines)) * 100

            return {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "ratio": round(ratio, 2)
            }

        except Exception as e:
            logger.warning(f"注释率计算失败: {e}")
            return {
                "total_lines": 0,
                "code_lines": 0,
                "comment_lines": 0,
                "ratio": 0,
                "error": str(e)
            }

    @staticmethod
    def _calculate_code_metrics(code: str) -> Dict[str, Any]:
        """计算代码度量指标"""
        try:
            from radon.raw import analyze

            # 使用 radon 的 raw 模块分析
            metrics = analyze(code)

            return {
                "loc": metrics.loc,  # 代码行数
                "lloc": metrics.lloc,  # 逻辑代码行数
                "sloc": metrics.sloc,  # 源代码行数
                "comments": metrics.comments,  # 注释行数
                "multi": metrics.multi,  # 多行字符串行数
                "blank": metrics.blank  # 空白行数
            }

        except Exception as e:
            logger.warning(f"代码度量失败: {e}")
            return {
                "loc": 0,
                "error": str(e)
            }

    @staticmethod
    def _calculate_quality_score(
        complexity: Dict[str, Any],
        maintainability: Dict[str, Any],
        comment_ratio: Dict[str, Any],
        code_metrics: Dict[str, Any]
    ) -> float:
        """
        计算综合质量评分（0-100）

        评分规则：
        - 可维护性指数：40%
        - 复杂度：30%
        - 注释率：20%
        - 代码规模：10%
        """
        score = 0

        # 1. 可维护性指数（40%）
        mi_score = maintainability.get("score", 0)
        score += (mi_score / 100) * 40

        # 2. 复杂度（30%）- 复杂度越低越好
        avg_complexity = complexity.get("average", 1)
        if avg_complexity <= 5:
            complexity_score = 100
        elif avg_complexity <= 10:
            complexity_score = 80
        elif avg_complexity <= 20:
            complexity_score = 60
        else:
            complexity_score = 40
        score += (complexity_score / 100) * 30

        # 3. 注释率（20%）- 10-30% 为最佳
        ratio = comment_ratio.get("ratio", 0)
        if 10 <= ratio <= 30:
            comment_score = 100
        elif 5 <= ratio < 10 or 30 < ratio <= 40:
            comment_score = 80
        elif ratio < 5:
            comment_score = 50
        else:
            comment_score = 60
        score += (comment_score / 100) * 20

        # 4. 代码规模（10%）- 适中的函数大小
        lloc = code_metrics.get("lloc", 0)
        if lloc <= 50:
            size_score = 100
        elif lloc <= 100:
            size_score = 90
        elif lloc <= 200:
            size_score = 80
        else:
            size_score = 70
        score += (size_score / 100) * 10

        return round(score, 2)

    @staticmethod
    def _get_quality_grade(score: float) -> str:
        """根据评分获取等级"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    @staticmethod
    def analyze_file_quality(file_path: str, code: str, language: str) -> Dict[str, Any]:
        """
        分析单个文件的代码质量

        Args:
            file_path: 文件路径
            code: 代码内容
            language: 编程语言

        Returns:
            包含文件路径和质量分析结果的字典
        """
        quality_result = CodeQualityAnalyzer.analyze_code_quality(code, language)
        quality_result["file_path"] = file_path

        return quality_result

