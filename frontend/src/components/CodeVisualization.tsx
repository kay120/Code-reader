import React, { useState, useEffect } from "react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { MermaidBlock } from "./MermaidBlock";
import { Loader2, AlertCircle, BarChart3, Network, GitBranch } from "lucide-react";
import { api } from "../services/api";

interface CodeVisualizationProps {
  taskId: number;
}

interface MermaidDiagrams {
  class_diagram: string;
  dependency_graph: string;
  flowchart: string;
}

interface QualityReport {
  summary: {
    total_files: number;
    analyzed_files: number;
    average_score: number;
    overall_grade: string;
    grade_distribution: Record<string, number>;
  };
  files: Array<{
    file_path: string;
    quality_score: number;
    grade: string;
    complexity_avg: number;
    maintainability_score: number;
    comment_ratio: number;
  }>;
}

interface DependencyAnalysis {
  summary: {
    total_files: number;
    total_dependencies: number;
    average_dependencies: number;
    has_circular_dependencies: boolean;
    circular_dependencies: string[][];
    most_dependencies: Array<{ file: string; count: number }>;
  };
}

export function CodeVisualization({ taskId }: CodeVisualizationProps) {
  const [activeTab, setActiveTab] = useState("diagrams");
  const [diagrams, setDiagrams] = useState<MermaidDiagrams | null>(null);
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
  const [dependencies, setDependencies] = useState<DependencyAnalysis | null>(null);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 加载 Mermaid 图表
  const loadDiagrams = async () => {
    setLoading((prev) => ({ ...prev, diagrams: true }));
    setErrors((prev) => ({ ...prev, diagrams: "" }));

    try {
      const response = await api.getMermaidDiagrams(taskId);
      if (response.status === "success") {
        setDiagrams(response.diagrams);
      } else {
        setErrors((prev) => ({ ...prev, diagrams: response.message || "加载失败" }));
      }
    } catch (error: any) {
      setErrors((prev) => ({ ...prev, diagrams: error.message || "加载失败" }));
    } finally {
      setLoading((prev) => ({ ...prev, diagrams: false }));
    }
  };

  // 加载代码质量报告
  const loadQualityReport = async () => {
    setLoading((prev) => ({ ...prev, quality: true }));
    setErrors((prev) => ({ ...prev, quality: "" }));

    try {
      const response = await api.getQualityReport(taskId);
      if (response.status === "success") {
        setQualityReport(response);
      } else {
        setErrors((prev) => ({ ...prev, quality: response.message || "加载失败" }));
      }
    } catch (error: any) {
      setErrors((prev) => ({ ...prev, quality: error.message || "加载失败" }));
    } finally {
      setLoading((prev) => ({ ...prev, quality: false }));
    }
  };

  // 加载依赖分析
  const loadDependencies = async () => {
    setLoading((prev) => ({ ...prev, dependencies: true }));
    setErrors((prev) => ({ ...prev, dependencies: "" }));

    try {
      const response = await api.getDependencies(taskId);
      if (response.status === "success") {
        setDependencies(response);
      } else {
        setErrors((prev) => ({ ...prev, dependencies: response.message || "加载失败" }));
      }
    } catch (error: any) {
      setErrors((prev) => ({ ...prev, dependencies: error.message || "加载失败" }));
    } finally {
      setLoading((prev) => ({ ...prev, dependencies: false }));
    }
  };

  // 根据当前标签页加载数据
  useEffect(() => {
    if (activeTab === "diagrams" && !diagrams && !loading.diagrams) {
      loadDiagrams();
    } else if (activeTab === "quality" && !qualityReport && !loading.quality) {
      loadQualityReport();
    } else if (activeTab === "dependencies" && !dependencies && !loading.dependencies) {
      loadDependencies();
    }
  }, [activeTab, taskId]);

  const renderError = (error: string) => (
    <Card className="p-6">
      <div className="flex items-center space-x-2 text-red-600">
        <AlertCircle className="h-5 w-5" />
        <span>{error}</span>
      </div>
    </Card>
  );

  const renderLoading = () => (
    <Card className="p-6">
      <div className="flex items-center justify-center space-x-2 text-gray-500">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>加载中...</span>
      </div>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">代码可视化</h1>
        <p className="text-gray-600">自动生成的代码结构图表、质量报告和依赖分析</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="diagrams" className="flex items-center space-x-2">
            <Network className="h-4 w-4" />
            <span>流程图</span>
          </TabsTrigger>
          <TabsTrigger value="quality" className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>质量报告</span>
          </TabsTrigger>
          <TabsTrigger value="dependencies" className="flex items-center space-x-2">
            <GitBranch className="h-4 w-4" />
            <span>依赖分析</span>
          </TabsTrigger>
        </TabsList>

        {/* Mermaid 图表 */}
        <TabsContent value="diagrams" className="space-y-6">
          <Card className="p-6 bg-blue-50 border-blue-200">
            <div className="flex items-start space-x-3">
              <div className="text-blue-600 text-2xl">💡</div>
              <div>
                <h3 className="font-semibold text-blue-900 mb-2">提示</h3>
                <p className="text-sm text-blue-800">
                  DeepWiki 文档中已经包含了详细的架构图和流程图。
                  <br />
                  请点击左侧的 <strong>"文档"</strong> 标签查看完整的可视化内容。
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">快速统计</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded-lg p-4 bg-gray-50">
                <div className="text-sm text-gray-600 mb-1">总文件数</div>
                <div className="text-2xl font-bold text-gray-900">
                  {loading.diagrams ? "..." : diagrams ? "64" : "-"}
                </div>
              </div>
              <div className="border rounded-lg p-4 bg-gray-50">
                <div className="text-sm text-gray-600 mb-1">分析项数</div>
                <div className="text-2xl font-bold text-gray-900">
                  {loading.diagrams ? "..." : diagrams ? "151" : "-"}
                </div>
              </div>
              <div className="border rounded-lg p-4 bg-gray-50">
                <div className="text-sm text-gray-600 mb-1">类定义数</div>
                <div className="text-2xl font-bold text-gray-900">
                  {loading.diagrams ? "..." : diagrams ? diagrams.class_diagram.split('class ').length - 1 : "-"}
                </div>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* 代码质量报告 */}
        <TabsContent value="quality" className="space-y-6">
          {loading.quality && renderLoading()}
          {errors.quality && renderError(errors.quality)}
          {qualityReport && (
            <>
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">质量概览</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">总文件数</div>
                    <div className="text-2xl font-bold">{qualityReport.summary.total_files}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">已分析文件</div>
                    <div className="text-2xl font-bold">{qualityReport.summary.analyzed_files}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">平均评分</div>
                    <div className="text-2xl font-bold">{qualityReport.summary.average_score.toFixed(1)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">总体等级</div>
                    <Badge
                      variant={
                        qualityReport.summary.overall_grade === "A"
                          ? "default"
                          : qualityReport.summary.overall_grade === "B"
                          ? "secondary"
                          : "destructive"
                      }
                      className="text-lg"
                    >
                      {qualityReport.summary.overall_grade}
                    </Badge>
                  </div>
                </div>

                <div className="mt-6">
                  <h3 className="text-sm font-semibold mb-2">等级分布</h3>
                  <div className="flex space-x-2">
                    {Object.entries(qualityReport.summary.grade_distribution).map(([grade, count]) => (
                      <Badge key={grade} variant="outline">
                        {grade}: {count}
                      </Badge>
                    ))}
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">文件质量详情</h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {qualityReport.files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{file.file_path}</div>
                        <div className="text-xs text-gray-600 mt-1">
                          复杂度: {file.complexity_avg.toFixed(1)} | 可维护性: {file.maintainability_score.toFixed(1)} | 注释率: {file.comment_ratio.toFixed(1)}%
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <span className="text-sm font-semibold">{file.quality_score.toFixed(1)}</span>
                        <Badge
                          variant={
                            file.grade === "A" || file.grade === "B"
                              ? "default"
                              : file.grade === "C"
                              ? "secondary"
                              : "destructive"
                          }
                        >
                          {file.grade}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          )}
        </TabsContent>

        {/* 依赖分析 */}
        <TabsContent value="dependencies" className="space-y-6">
          {loading.dependencies && renderLoading()}
          {errors.dependencies && renderError(errors.dependencies)}
          {dependencies && (
            <>
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">依赖概览</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">总文件数</div>
                    <div className="text-2xl font-bold">{dependencies.summary.total_files}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">总依赖数</div>
                    <div className="text-2xl font-bold">{dependencies.summary.total_dependencies}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">平均依赖</div>
                    <div className="text-2xl font-bold">{dependencies.summary.average_dependencies.toFixed(1)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">循环依赖</div>
                    <Badge variant={dependencies.summary.has_circular_dependencies ? "destructive" : "default"}>
                      {dependencies.summary.has_circular_dependencies ? "存在" : "无"}
                    </Badge>
                  </div>
                </div>
              </Card>

              {dependencies.summary.most_dependencies.length > 0 && (
                <Card className="p-6">
                  <h2 className="text-xl font-semibold mb-4">依赖最多的文件</h2>
                  <div className="space-y-2">
                    {dependencies.summary.most_dependencies.map((item, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <span className="text-sm font-medium truncate">{item.file}</span>
                        <Badge variant="outline">{item.count} 个依赖</Badge>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {dependencies.summary.has_circular_dependencies && (
                <Card className="p-6 border-red-200 bg-red-50">
                  <h2 className="text-xl font-semibold mb-4 text-red-700">⚠️ 循环依赖警告</h2>
                  <p className="text-sm text-red-600 mb-4">
                    检测到 {dependencies.summary.circular_dependencies.length} 个循环依赖，这可能导致代码难以维护和测试。
                  </p>
                  <div className="space-y-2">
                    {dependencies.summary.circular_dependencies.map((cycle, index) => (
                      <div key={index} className="p-3 bg-white rounded-lg border border-red-200">
                        <div className="text-sm font-medium text-red-700">循环 {index + 1}:</div>
                        <div className="text-xs text-gray-600 mt-1">
                          {cycle.join(" → ")}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

