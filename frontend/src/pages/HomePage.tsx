import { useState, useEffect } from "react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Loader2,
  RefreshCw,
  Database,
  TrendingUp,
  Users,
  Shield,
  Upload,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import ProjectCard from "../components/ProjectCard";
import ProjectCardSkeleton from "../components/ProjectCardSkeleton";
import {
  api,
  RepositoryListResponse,
  RepositoryListItem,
} from "../services/api";

export default function HomePage() {
  const [repositories, setRepositories] = useState<RepositoryListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(12); // 每页显示12个项目

  // 获取项目列表
  const fetchRepositories = async (page: number = 1) => {
    try {
      setLoading(true);
      setError(null);

      // 添加超时控制 - 15秒超时
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      const response: RepositoryListResponse = await api.getRepositoriesList(
        {
          page,
          page_size: pageSize,
          order_by: "updated_at",
          order_direction: "desc",
          status: 1, // 只显示正常状态的项目
        },
        controller.signal
      );

      clearTimeout(timeoutId);

      if (response.status === "success") {
        setRepositories(response.data.repositories);
        setCurrentPage(response.data.pagination.current_page);
        setTotalPages(response.data.pagination.total_pages);
        setTotalCount(response.data.pagination.total_count);
      } else {
        setError(response.message || "获取项目列表失败");
      }
    } catch (err: any) {
      console.error("获取项目列表失败:", err);
      if (err.name === 'AbortError') {
        setError("请求超时,后端可能正在处理分析任务,请稍后刷新");
      } else {
        setError("网络错误，请稍后重试");
      }
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    fetchRepositories(1);
  }, []);

  // 处理页码变化
  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      fetchRepositories(page);
    }
  };

  // 刷新数据
  const handleRefresh = () => {
    fetchRepositories(currentPage);
  };

  // 渲染分页控件
  const renderPagination = () => {
    if (totalPages <= 1) return null;

    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return (
      <div
        className="flex items-center justify-center space-x-2 mt-8"
        style={{ marginTop: "2rem", paddingBottom: "2rem" }}
      >
        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
        >
          <ChevronLeft className="w-4 h-4" />
        </Button>

        {pages.map((page) => (
          <Button
            key={page}
            variant={page === currentPage ? "default" : "outline"}
            size="sm"
            onClick={() => handlePageChange(page)}
          >
            {page}
          </Button>
        ))}

        <Button
          variant="outline"
          size="sm"
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    );
  };

  return (
    <div
      className="min-h-full bg-gradient-to-br from-blue-50 via-white to-purple-50"
      style={{ height: "calc(100vh - 57px)" }}
    >
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 头部区域 */}
        <div className="text-center mb-12" style={{ paddingTop: "3rem" }}>
          <h1
            className="text-4xl font-bold text-gray-900 mb-4"
            style={{ fontSize: "2.5rem" }}
          >
            AI 代码库领航员
          </h1>
          <p className="text-xl text-gray-600 mb-12">
            智能分析您的代码库，生成详细的技术文档
          </p>

          {/* 统计信息 */}
          <div
            className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
            style={{ marginTop: "3rem" }}
          >
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-center mb-2">
                <Database className="w-8 h-8 text-blue-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {loading ? (
                  <div className="h-8 w-16 bg-gray-200 rounded animate-pulse mx-auto" />
                ) : (
                  totalCount
                )}
              </div>
              <div className="text-sm text-gray-600">项目总数</div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-center mb-2">
                <TrendingUp className="w-8 h-8 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {loading ? (
                  <div className="h-8 w-16 bg-gray-200 rounded animate-pulse mx-auto" />
                ) : (
                  repositories.reduce(
                    (sum, repo) => {
                      // 统计所有任务数量
                      const taskCount = repo.tasks ? repo.tasks.length : 0;
                      return sum + taskCount;
                    },
                    0
                  )
                )}
              </div>
              <div className="text-sm text-gray-600">分析任务总数</div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-center mb-2">
                <Loader2 className="w-8 h-8 text-orange-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {loading ? (
                  <div className="h-8 w-16 bg-gray-200 rounded animate-pulse mx-auto" />
                ) : (
                  repositories.reduce(
                    (sum, repo) => {
                      // 统计正在运行的任务数量（包括 running 和 processing 状态）
                      const runningCount = repo.tasks
                        ? repo.tasks.filter((task: any) => task.status === "running" || task.status === "processing").length
                        : 0;
                      return sum + runningCount;
                    },
                    0
                  )
                )}
              </div>
              <div className="text-sm text-gray-600">正在处理</div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-center mb-2">
                <Shield className="w-8 h-8 text-purple-600" />
              </div>
              <div className="text-2xl font-bold text-gray-900">100%</div>
              <div className="text-sm text-gray-600">本地处理</div>
            </div>
          </div>
        </div>

        {/* 操作栏 */}
        <div
          className="flex items-center justify-between my-12"
          style={{ marginTop: "3rem", marginBottom: "3rem" }}
        >
          <div className="flex items-center space-x-4">
            <h2 className="text-2xl font-semibold text-gray-900">项目列表</h2>
            <Badge variant="secondary">共 {totalCount} 个项目</Badge>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw
                className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
              />
              刷新
            </Button>

            <Button
              onClick={() => (window.location.href = "/upload")}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Upload className="w-4 h-4 mr-2" />
              上传新项目
            </Button>
          </div>
        </div>

        {/* 内容区域 */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {Array.from({ length: pageSize }).map((_, index) => (
              <ProjectCardSkeleton key={index} />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertCircle className={`w-12 h-12 mx-auto mb-4 ${
              error.includes('超时') ? 'text-orange-500' : 'text-red-500'
            }`} />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {error.includes('超时') ? '加载超时' : '加载失败'}
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            {error.includes('超时') && (
              <p className="text-sm text-gray-500 mb-4">
                💡 提示: 后端正在处理分析任务,请稍后再试
              </p>
            )}
            <Button onClick={handleRefresh} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              重试
            </Button>
          </div>
        ) : repositories.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无项目</h3>
            <p className="text-gray-600 mb-4">
              还没有上传任何项目，开始上传您的第一个项目吧！
            </p>
            <Button
              onClick={() => (window.location.href = "/upload")}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Upload className="w-4 h-4 mr-2" />
              上传项目
            </Button>
          </div>
        ) : (
          <>
            {/* 项目网格 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {repositories.map((repository) => (
                <ProjectCard
                  key={repository.id}
                  repository={repository}
                  onDelete={handleRefresh}
                />
              ))}
            </div>

            {/* 分页 */}
            {renderPagination()}
          </>
        )}
      </div>
    </div>
  );
}
