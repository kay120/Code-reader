import React, { useState, useEffect, useCallback } from "react";
import { Button } from "./ui/button";
import { Sidebar } from "./DeepWikiSidebar";
import { MainContent } from "./DeepWikiMainContent";
import { FileExplorer } from "./FileExplorer";
import CodeViewer from "./CodeViewer";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { api } from "../services/api";
import {
    buildFileTree,
    sortFileTree,
    FileNode,
    findFileInTree,
    getPathsToExpand,
    normalizePath,
    debugPrintFileTree,
    findAllFilesByName,
    findFileFullPath,
} from "../utils/fileTree";
import { useProject } from "../contexts/ProjectContext";

interface DeepWikiInterfaceProps {
    onBackToUpload: () => void;
    onGoToProfile: () => void;
    currentVersionId?: string;
    fullNameHash?: string; // 改为fullNameHash，表示这是仓库的full_name哈希值
}

type ViewMode = "documentation" | "code";

export default function DeepWikiInterface({
    onBackToUpload,
    onGoToProfile,
    currentVersionId,
    fullNameHash,
}: DeepWikiInterfaceProps) {
    const { setCurrentRepository } = useProject();
    const [activeSection, setActiveSection] = useState("overview");
    
    // 使用 useCallback 稳定 setActiveSection，避免不必要的子组件重新渲染
    const handleSectionChange = useCallback((section: string) => {
        setActiveSection(section);
    }, []);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [isFileExplorerVisible, setIsFileExplorerVisible] = useState(true);
    const [viewMode, setViewMode] = useState<ViewMode>("documentation");

    // 新增：文件高亮相关状态
    const [highlightedFile, setHighlightedFile] = useState<string | null>(null);
    const [expandedPaths, setExpandedPaths] = useState<string[]>([]);

    // 新增状态
    const [fileTree, setFileTree] = useState<FileNode | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [repositoryInfo, setRepositoryInfo] = useState<any>(null);
    const [fileDataMap, setFileDataMap] = useState<Map<string, any>>(new Map());
    const [selectedFileAnalysisId, setSelectedFileAnalysisId] = useState<
        number | undefined
    >(undefined);
    const [taskStatistics, setTaskStatistics] = useState<{
        code_lines: number;
        total_files: number;
        module_count: number;
    } | null>(null);
    const [currentTaskId, setCurrentTaskId] = useState<number | null>(null);
    const [completedFiles, setCompletedFiles] = useState<Set<string>>(new Set());
    const [pendingFiles, setPendingFiles] = useState<Set<string>>(new Set());

    // 使用 useCallback 优化，避免每次渲染都创建新函数
    const handleFileSelect = useCallback((filePath: string) => {
        console.log("File selected:", filePath);
        console.log("Available files in map:", Array.from(fileDataMap.keys()));

        setSelectedFile(filePath);
        setViewMode("code");

        // 从文件数据映射中获取对应的file_analysis_id
        const fileData = fileDataMap.get(filePath);
        console.log("File data found:", fileData);

        if (fileData && fileData.id) {
            setSelectedFileAnalysisId(fileData.id);
            console.log(
                "Selected file analysis ID:",
                fileData.id,
                "for file:",
                filePath
            );
        } else {
            setSelectedFileAnalysisId(undefined);
            console.warn("No file analysis ID found for file:", filePath);
            console.warn("File data map contents:", fileDataMap);
        }
    }, [fileDataMap]);

    // 新增：处理文件高亮定位 - 使用 useCallback 优化
    const handleFileHighlight = useCallback((filePath: string) => {
        console.log("File highlight requested:", filePath);

        // 标准化文件路径：URL解码 + 路径分隔符标准化
        const normalizedPath = normalizePath(filePath);
        console.log("Normalized path:", normalizedPath);

        // 调试：打印文件树结构
        console.log("=== File Tree Structure ===");
        debugPrintFileTree(fileTree);

        // 调试：查找所有匹配的文件
        const isFileNameOnly = !normalizedPath.includes("/");
        if (isFileNameOnly) {
            console.log(`=== Searching for file name: "${normalizedPath}" ===`);
            const matches = findAllFilesByName(fileTree, normalizedPath);
            console.log("Found matches:", matches);
        }

        // 检查文件是否存在于文件树中
        const fileExists = findFileInTree(fileTree, normalizedPath);
        console.log("File exists:", fileExists);

        if (!fileExists) {
            console.warn("File not found in tree:", normalizedPath);
            return;
        }

        // 获取文件的完整路径（对于只有文件名的情况很重要）
        const fullPath = findFileFullPath(fileTree, normalizedPath);
        console.log("Full path found:", fullPath);

        if (!fullPath) {
            console.warn("Could not determine full path for:", normalizedPath);
            return;
        }

        // 确保文件浏览器可见
        setIsFileExplorerVisible(true);

        // 设置高亮文件（使用完整路径）
        setHighlightedFile(fullPath);

        // 获取需要展开的路径（使用完整路径）
        const pathsToExpand = getPathsToExpand(fileTree, fullPath);
        setExpandedPaths(pathsToExpand);

        console.log(
            "File highlighted:",
            fullPath,
            "Original path:",
            filePath,
            "Normalized path:",
            normalizedPath,
            "Paths to expand:",
            pathsToExpand
        );

        // 保持高亮状态，不自动清除
        // setTimeout(() => {
        //   setHighlightedFile(null);
        // }, 3000);
    }, [fileTree]);

    const handleBackToDocumentation = () => {
        setViewMode("documentation");
        setSelectedFile(null);
    };

    // 数据加载函数 - 优化版：并行加载 + 懒加载
    const loadProjectData = async (fullNameHash: string) => {
        if (!fullNameHash) return;

        setIsLoading(true);
        setError(null);

        try {
            // 1. 通过full_name获取仓库信息
            console.log("Loading repository data for full_name:", fullNameHash);
            const repoResponse = await api.getRepositoryById(
                Number(fullNameHash)
            );
            console.log("Repository API response:", repoResponse);

            if (repoResponse.status !== "success" || !repoResponse.repository) {
                throw new Error(
                    `Repository with full_name "${fullNameHash}" not found`
                );
            }

            const repository = repoResponse.repository;
            console.log("Repository data:", repository);
            setRepositoryInfo(repository);
            // 同时设置到全局Context中，供TopNavigation使用
            setCurrentRepository(repository);

            // 2. 获取该仓库的分析任务列表
            console.log(
                "Loading analysis tasks for repository ID:",
                repository.id
            );
            const tasksResponse = await api.getAnalysisTasksByRepositoryId(
                repository.id
            );
            console.log("Tasks API response:", tasksResponse);

            if (
                tasksResponse.status !== "success" ||
                !tasksResponse.tasks ||
                tasksResponse.tasks.length === 0
            ) {
                console.warn("No analysis tasks found for this repository");
                setIsLoading(false);
                return;
            }

            // 3. 找到最新的任务（按start_time降序排序，取第一个）
            const sortedTasks = tasksResponse.tasks.sort(
                (a, b) =>
                    new Date(b.start_time).getTime() -
                    new Date(a.start_time).getTime()
            );
            const latestTask = sortedTasks[0]; // 取最新的任务

            console.log("Latest task found:", latestTask);

            // 4. 设置当前任务ID（立即设置，让 README 可以开始加载）
            setCurrentTaskId(latestTask.id);

            // 5. 提取任务统计信息（立即显示）
            console.log("🔍 [DEBUG] latestTask 完整数据:", latestTask);
            console.log("🔍 [DEBUG] latestTask.code_lines:", latestTask.code_lines);
            console.log("🔍 [DEBUG] latestTask.module_count:", latestTask.module_count);

            const statistics = {
                code_lines: latestTask.code_lines || 0,
                total_files: latestTask.total_files || 0,
                module_count: latestTask.module_count || 0,
            };
            setTaskStatistics(statistics);
            console.log("🔍 [DEBUG] Task statistics 设置为:", statistics);

            // 6. 立即结束 loading 状态，让页面可以显示
            setIsLoading(false);

            // 7. 异步加载文件列表（不阻塞页面显示）
            console.log("Loading files for task ID:", latestTask.id);
            api.getFilesByTaskId(latestTask.id).then((filesResponse) => {
                console.log("Files API response:", filesResponse);

                if (filesResponse.status === "success") {
                    if (
                        filesResponse.files &&
                        Array.isArray(filesResponse.files) &&
                        filesResponse.files.length > 0
                    ) {
                        // 构建文件数据映射 + 收集已分析和未分析的文件
                        const dataMap = new Map();
                        const completedSet = new Set<string>();
                        const pendingSet = new Set<string>();

                        console.log("🔍 开始处理文件列表，总数:", filesResponse.files.length);
                        console.log("🔍 前3个文件的原始数据:", filesResponse.files.slice(0, 3));

                        filesResponse.files.forEach((file: any, index: number) => {
                            // 统一路径格式：将反斜杠转换为正斜杠，与文件树保持一致
                            const normalizedPath = file.file_path.replace(
                                /\\/g,
                                "/"
                            );

                            // 优先保留 status = "success" 的记录
                            // 如果已有记录且是 success，则不覆盖
                            // 如果新记录是 success，则覆盖旧记录
                            const existingFile = dataMap.get(normalizedPath);
                            if (!existingFile ||
                                (file.status === "success" && existingFile.status !== "success")) {
                                dataMap.set(normalizedPath, file);
                            }

                            // 打印前3个文件的 status 字段
                            if (index < 3) {
                                console.log(`  文件 ${index}: ${normalizedPath}`);
                                console.log(`    file.status = "${file.status}"`);
                                console.log(`    file.analysis_status = "${file.analysis_status}"`);
                                console.log(`    所有字段:`, Object.keys(file));
                            }
                        });

                        // 根据最终保存到 dataMap 的记录来分类文件状态
                        dataMap.forEach((file, normalizedPath) => {
                            // success 或 completed 都表示已完成
                            if (file.status === "success" || file.status === "completed") {
                                completedSet.add(normalizedPath);
                            } else {
                                // pending, failed, 或其他状态都显示红点
                                pendingSet.add(normalizedPath);
                            }
                        });

                        setFileDataMap(dataMap);
                        setCompletedFiles(completedSet);
                        setPendingFiles(pendingSet);
                        console.log("File data map built:", dataMap);
                        console.log("Completed files:", completedSet.size, "files");
                        console.log("Pending files:", pendingSet.size, "files");

                        // 构建文件树
                        console.log(
                            "Building file tree from files:",
                            filesResponse.files
                        );
                        const tree = buildFileTree(filesResponse.files);
                        sortFileTree(tree);
                        setFileTree(tree);
                        console.log("File tree built:", tree);
                    } else {
                        console.warn("No files found for task:", latestTask.id);
                        setFileTree(null);
                        setFileDataMap(new Map());
                    }
                } else {
                    console.error("Files API returned error:", filesResponse);
                }
            }).catch((err) => {
                console.error("Error loading files:", err);
                setFileTree(null);
                setFileDataMap(new Map());
            });

        } catch (err) {
            console.error("Error loading project data:", err);
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to load project data"
            );
            setIsLoading(false);
        }
    };

    // 当fullNameHash改变时加载数据
    useEffect(() => {
        if (fullNameHash && fullNameHash !== "my-awesome-project") {
            loadProjectData(fullNameHash);
        }
    }, [fullNameHash]);

    // 注释掉组件卸载时清理Context状态，因为切换到 chat 页面时需要保留 currentRepository
    // useEffect(() => {
    //     return () => {
    //         setCurrentRepository(null);
    //     };
    // }, [setCurrentRepository]);

    return (
        <div className="h-full flex flex-col bg-white">
            {/* Main Layout */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left Sidebar - DeepWiki Navigation (only show in documentation mode) */}
                {viewMode === "documentation" && (
                    <aside className="w-64 border-r border-gray-200 bg-gray-50 overflow-y-auto">
                        <Sidebar
                            activeSection={activeSection}
                            onSectionChange={handleSectionChange}
                            taskId={currentTaskId}
                        />
                    </aside>
                )}

                {/* Main Content Area */}
                <main
                    className={`flex-1 overflow-y-auto ${
                        isFileExplorerVisible ? "mr-80" : ""
                    }`}
                >
                    {viewMode === "documentation" ? (
                        <MainContent
                            activeSection={activeSection}
                            onSectionChange={handleSectionChange}
                            onFileSelect={handleFileSelect}
                            onFileHighlight={handleFileHighlight}
                            fileTree={fileTree}
                            projectName={repositoryInfo?.name || fullNameHash}
                            taskStatistics={taskStatistics}
                            taskId={currentTaskId}
                            repositoryInfo={repositoryInfo}
                        />
                    ) : (
                        selectedFile && (
                            <CodeViewer
                                filePath={selectedFile}
                                fileAnalysisId={selectedFileAnalysisId}
                                taskId={currentTaskId}
                                onBack={handleBackToDocumentation}
                            />
                        )
                    )}
                </main>

                {/* Right Sidebar - File Explorer */}
                <aside
                    className={`
            w-80 border-l border-gray-200 bg-gray-50 flex flex-col transition-all duration-300
            ${isFileExplorerVisible ? "translate-x-0" : "translate-x-full"}
            fixed right-0 top-[73px] bottom-0 z-10
          `}
                >
                    <div className="flex items-center justify-between p-4 border-b border-gray-200">
                        <div>
                            <h3 className="font-medium text-gray-900">
                                源代码浏览器
                            </h3>
                            {fullNameHash &&
                                fullNameHash !== "my-awesome-project" && (
                                    <p className="text-xs text-gray-500 mt-1">
                                        {repositoryInfo
                                            ? `${repositoryInfo.name}`
                                            : fullNameHash}
                                    </p>
                                )}
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                                setIsFileExplorerVisible(!isFileExplorerVisible)
                            }
                        >
                            {isFileExplorerVisible ? (
                                <ChevronRight className="h-4 w-4" />
                            ) : (
                                <ChevronLeft className="h-4 w-4" />
                            )}
                        </Button>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        <FileExplorer
                            selectedFile={selectedFile}
                            onFileSelect={handleFileSelect}
                            fileTree={fileTree}
                            isLoading={isLoading}
                            error={error}
                            highlightedFile={highlightedFile}
                            expandedPaths={expandedPaths}
                            taskId={currentTaskId}
                            completedFiles={completedFiles}
                            pendingFiles={pendingFiles}
                        />
                    </div>
                </aside>

                {/* Toggle button when file explorer is hidden */}
                {!isFileExplorerVisible && (
                    <Button
                        variant="outline"
                        size="sm"
                        className="fixed right-4 top-[85px] z-20"
                        onClick={() => setIsFileExplorerVisible(true)}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                )}
            </div>
        </div>
    );
}
