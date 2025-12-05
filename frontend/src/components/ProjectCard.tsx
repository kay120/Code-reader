import { useNavigate } from "react-router-dom";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader } from "./ui/card";
import {
    Folder,
    Calendar,
    Clock,
    CheckCircle,
    XCircle,
    AlertCircle,
    User,
    Trash2,
} from "lucide-react";
import { RepositoryListItem } from "../services/api";
import { useState } from "react";

interface ProjectCardProps {
    repository: RepositoryListItem;
    onDelete?: () => void;
}

export default function ProjectCard({ repository, onDelete }: ProjectCardProps) {
    const navigate = useNavigate();
    const [isDeleting, setIsDeleting] = useState(false);

    const handleClick = () => {
        navigate(`/result/${repository.id}`);
    };

    const handleDelete = async (e: React.MouseEvent) => {
        e.stopPropagation(); // 阻止事件冒泡,避免触发卡片点击

        if (!confirm(`确定要删除仓库 "${repository.name}" 吗?`)) {
            return;
        }

        setIsDeleting(true);
        try {
            const response = await fetch(
                `http://localhost:8000/api/repository/repositories/${repository.id}?soft_delete=false`,
                {
                    method: "DELETE",
                }
            );

            if (response.ok) {
                // 调用父组件的回调函数刷新列表
                if (onDelete) {
                    onDelete();
                }
            } else {
                const error = await response.json();
                alert(`删除失败: ${error.message || "未知错误"}`);
            }
        } catch (error) {
            console.error("删除仓库失败:", error);
            alert("删除失败,请稍后重试");
        } finally {
            setIsDeleting(false);
        }
    };

    const getStatusBadge = () => {
        if (repository.status === 1) {
            return (
                <Badge
                    variant="default"
                    className="bg-green-100 text-green-800 hover:bg-green-100"
                >
                    <CheckCircle className="w-3 h-3 mr-1" />
                    正常
                </Badge>
            );
        } else {
            return (
                <Badge
                    variant="destructive"
                    className="bg-red-100 text-red-800 hover:bg-red-100"
                >
                    <XCircle className="w-3 h-3 mr-1" />
                    已删除
                </Badge>
            );
        }
    };

    const getTaskStatusInfo = () => {
        if (!repository.tasks || repository.tasks.length === 0) {
            return (
                <div className="flex items-center text-sm text-gray-500">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    暂无分析任务
                </div>
            );
        }

        const latestTask = repository.tasks[0]; // 假设任务按时间排序
        const statusMap = {
            pending: { text: "等待中", color: "text-yellow-600", icon: Clock },
            running: { text: "分析中", color: "text-blue-600", icon: Clock },
            processing: { text: "分析中", color: "text-blue-600", icon: Clock },
            completed: {
                text: "已完成",
                color: "text-green-600",
                icon: CheckCircle,
            },
            failed: { text: "失败", color: "text-red-600", icon: XCircle },
        };

        const status =
            statusMap[latestTask.status as keyof typeof statusMap] ||
            statusMap.pending;
        const StatusIcon = status.icon;

        // 如果是运行中或处理中,显示进度
        if (latestTask.status === "running" || latestTask.status === "processing") {
            // 根据文件进度和task_index判断当前步骤和整体进度
            const successfulFiles = latestTask.successful_files || 0;
            const totalFiles = latestTask.total_files || 0;
            const analysisSuccess = latestTask.analysis_success_files || 0;
            const analysisTotal = latestTask.analysis_total_files || 0;

            let currentStep = 0;
            let stepProgress = 0;
            let statusText = "扫描文件中";
            let detailText = `${successfulFiles}/${totalFiles}`;

            if (successfulFiles === totalFiles && totalFiles > 0) {
                // 文件扫描完成
                if (analysisTotal > 0) {
                    // 正在分析数据模型
                    currentStep = 2;
                    const analysisProgress = analysisTotal > 0 ? (analysisSuccess / analysisTotal) * 100 : 0;
                    stepProgress = 25 + Math.round(analysisProgress * 0.5); // 步骤2占50%
                    statusText = "分析数据模型";
                    detailText = `${analysisSuccess}/${analysisTotal}`;
                } else if (latestTask.task_index) {
                    currentStep = 1; // 知识库已创建
                    stepProgress = 25;
                    statusText = "创建知识库";
                    detailText = "步骤 1/4";
                } else {
                    currentStep = 1; // 正在创建知识库
                    stepProgress = 25;
                    statusText = "创建知识库";
                    detailText = "步骤 1/4";
                }
            } else if (successfulFiles > 0) {
                // 正在扫描文件
                currentStep = 0;
                stepProgress = Math.round((successfulFiles / totalFiles) * 25); // 步骤0占25%
                statusText = "扫描文件中";
                detailText = `${successfulFiles}/${totalFiles}`;
            }

            return (
                <div className="space-y-1">
                    <div className={`flex items-center text-sm ${status.color}`}>
                        <StatusIcon className="w-4 h-4 mr-1 animate-spin" />
                        {statusText} ({detailText})
                    </div>
                    {totalFiles > 0 && (
                        <div className="flex items-center space-x-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                                <div
                                    className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                    style={{ width: `${stepProgress}%` }}
                                />
                            </div>
                            <span className="text-xs text-blue-600 font-medium">{stepProgress}%</span>
                        </div>
                    )}
                </div>
            );
        }

        // 如果是失败状态,但文件都分析完了,显示"部分完成"
        if (latestTask.status === "failed" &&
            latestTask.successful_files === latestTask.total_files &&
            latestTask.total_files > 0) {
            return (
                <div className="space-y-1">
                    <div className="flex items-center text-sm text-orange-600">
                        <AlertCircle className="w-4 h-4 mr-1" />
                        文件分析完成
                    </div>
                    <div className="text-xs text-gray-500">
                        文档生成失败,但可查看文件分析结果
                    </div>
                </div>
            );
        }

        return (
            <div className={`flex items-center text-sm ${status.color}`}>
                <StatusIcon className="w-4 h-4 mr-1" />
                最新任务: {status.text}
            </div>
        );
    };

    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString("zh-CN", {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return dateString;
        }
    };

    return (
        <Card
            className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] border border-gray-200 hover:border-blue-300 relative group"
            onClick={handleClick}
        >
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <Folder className="w-5 h-5 text-blue-600 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                            <h3
                                className="font-semibold text-gray-900 truncate"
                                title={repository.name}
                            >
                                {repository.name}
                            </h3>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {getStatusBadge()}
                        {/* 删除按钮 */}
                        <Button
                            variant="ghost"
                            size="sm"
                            className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600"
                            onClick={handleDelete}
                            disabled={isDeleting}
                            title="删除仓库"
                        >
                            <Trash2 className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="pt-0">
                <div className="space-y-3">
                    {/* 任务状态信息 */}
                    {getTaskStatusInfo()}

                    {/* 统计信息 */}
                    {repository.total_tasks !== undefined && (
                        <div className="flex items-center text-sm text-gray-600">
                            <User className="w-4 h-4 mr-1" />共{" "}
                            {repository.total_tasks} 个分析任务
                        </div>
                    )}

                    {/* 时间信息 */}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            创建: {formatDate(repository.created_at)}
                        </div>
                        <div className="flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            更新: {formatDate(repository.updated_at)}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
