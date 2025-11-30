import { useState, useEffect } from "react";
import { ChevronDown, ChevronRight, File, Folder } from "lucide-react";
import { Button } from "./ui/button";
import { api } from "../services/api";

interface FileNode {
  name: string;
  type: "file" | "folder";
  path: string;
  children?: FileNode[];
}

interface FileExplorerProps {
  selectedFile: string | null;
  onFileSelect: (path: string) => void;
  fileTree?: FileNode | null;
  isLoading?: boolean;
  error?: string | null;
  highlightedFile?: string | null; // 新增：需要高亮的文件路径
  expandedPaths?: string[]; // 新增：需要展开的文件夹路径
  taskId?: number | null; // 新增：任务ID用于获取进度
  completedFiles?: Set<string>; // 新增：已完成AI分析的文件路径集合
  pendingFiles?: Set<string>; // 新增：未完成AI分析的文件路径集合
}

const mockFileTree: FileNode = {
  name: "src",
  type: "folder",
  path: "src",
  children: [
    {
      name: "api",
      type: "folder",
      path: "src/api",
      children: [
        { name: "routes.py", type: "file", path: "src/api/routes.py" },
        { name: "auth.py", type: "file", path: "src/api/auth.py" },
        { name: "posts.py", type: "file", path: "src/api/posts.py" },
        { name: "users.py", type: "file", path: "src/api/users.py" },
      ],
    },
    {
      name: "models",
      type: "folder",
      path: "src/models",
      children: [
        { name: "user.py", type: "file", path: "src/models/user.py" },
        { name: "post.py", type: "file", path: "src/models/post.py" },
        { name: "__init__.py", type: "file", path: "src/models/__init__.py" },
      ],
    },
    {
      name: "services",
      type: "folder",
      path: "src/services",
      children: [
        {
          name: "auth_service.py",
          type: "file",
          path: "src/services/auth_service.py",
        },
        {
          name: "post_service.py",
          type: "file",
          path: "src/services/post_service.py",
        },
      ],
    },
    {
      name: "utils",
      type: "folder",
      path: "src/utils",
      children: [
        { name: "helpers.py", type: "file", path: "src/utils/helpers.py" },
        {
          name: "validators.py",
          type: "file",
          path: "src/utils/validators.py",
        },
      ],
    },
    { name: "app.py", type: "file", path: "src/app.py" },
    { name: "config.py", type: "file", path: "src/config.py" },
  ],
};

function FileTreeNode({
  node,
  level = 0,
  selectedFile,
  onFileSelect,
  highlightedFile,
  expandedPaths,
  completedFiles,
  pendingFiles,
}: {
  node: FileNode;
  level?: number;
  selectedFile: string | null;
  onFileSelect: (path: string) => void;
  highlightedFile?: string | null;
  expandedPaths?: string[];
  completedFiles?: Set<string>;
  pendingFiles?: Set<string>;
}) {
  // 判断是否应该展开：默认展开前2层，或者在expandedPaths中
  const shouldExpand =
    level < 2 || (expandedPaths && expandedPaths.includes(node.path));
  const [isExpanded, setIsExpanded] = useState(shouldExpand);

  // 当expandedPaths改变时，更新展开状态
  useEffect(() => {
    if (expandedPaths && expandedPaths.includes(node.path)) {
      setIsExpanded(true);
    }
  }, [expandedPaths, node.path]);

  const isSelected = selectedFile === node.path;
  const isHighlighted = highlightedFile === node.path;
  const isCompleted = node.type === "file" && completedFiles?.has(node.path);
  const isPending = node.type === "file" && pendingFiles?.has(node.path);

  // 调试：打印路径匹配信息
  if (highlightedFile && node.type === "file") {
    console.log(
      `File node: "${node.name}" (path: "${node.path}"), highlighted: "${highlightedFile}", match: ${isHighlighted}`
    );
  }

  const handleClick = () => {
    if (node.type === "folder") {
      setIsExpanded(!isExpanded);
    } else {
      onFileSelect(node.path);
    }
  };

  return (
    <div>
      <Button
        variant="ghost"
        className={`
          w-full justify-start px-2 py-1 h-auto text-sm transition-all duration-300
          ${
            isSelected
              ? "bg-blue-100 text-blue-700"
              : isHighlighted
              ? "bg-yellow-100 text-yellow-800 border-2 border-yellow-300"
              : isPending
              ? "text-yellow-600 hover:bg-yellow-50"
              : isCompleted
              ? "text-gray-900 hover:bg-gray-100"
              : "text-gray-700 hover:bg-gray-100"
          }
        `}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
      >
        {node.type === "folder" && (
          <>
            {isExpanded ? (
              <ChevronDown className="h-3 w-3 mr-1" />
            ) : (
              <ChevronRight className="h-3 w-3 mr-1" />
            )}
            <Folder className="h-4 w-4 mr-2 text-blue-500" />
          </>
        )}
        {node.type === "file" && (
          <File
            className={`h-4 w-4 mr-2 ml-4 ${
              isPending
                ? "text-yellow-500"
                : isCompleted
                ? "text-gray-700"
                : "text-gray-500"
            }`}
          />
        )}
        <span className={`truncate ${
          isPending
            ? "font-medium"
            : isCompleted
            ? "font-normal"
            : ""
        }`}>
          {node.name}
        </span>
        {isPending && (
          <div
            className="ml-2 w-2 h-2 rounded-full bg-yellow-500 animate-pulse flex-shrink-0"
            title="AI分析中..."
          />
        )}
      </Button>

      {node.type === "folder" && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode
              key={child.path}
              node={child}
              level={level + 1}
              selectedFile={selectedFile}
              onFileSelect={onFileSelect}
              highlightedFile={highlightedFile}
              expandedPaths={expandedPaths}
              completedFiles={completedFiles}
              pendingFiles={pendingFiles}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function FileExplorer({
  selectedFile,
  onFileSelect,
  fileTree,
  isLoading,
  error,
  highlightedFile,
  expandedPaths,
  taskId,
  completedFiles,
  pendingFiles,
}: FileExplorerProps) {
  const [taskStatus, setTaskStatus] = useState<any>(null);
  const [progressMessage, setProgressMessage] = useState<string>("正在生成中...");

  // 检查任务状态
  useEffect(() => {
    if (!taskId || !error) return;

    const checkStatus = async () => {
      try {
        console.log("[FileExplorer] 检查任务状态, taskId:", taskId);

        const result = await api.getAnalysisTaskDetail(taskId);
        if (result.status !== "success" || !result.task) {
          console.warn("[FileExplorer] 未获取到任务详情:", result);
          return;
        }

        const task = result.task;
        setTaskStatus(task);

        // 根据任务状态生成更细致的进度文案
        if (task.status === "running") {
          const totalFiles = task.total_files || 0;
          const successfulFiles = task.successful_files || 0;
          const analysisTotal = task.analysis_total_files || 0;
          const analysisSuccess = task.analysis_success_files || 0;
          const analysisProgress = task.analysis_progress || 0;

          let step = 0;
          let message = "正在扫描代码文件...";

          // 步骤0: 扫描代码文件
          if (totalFiles > 0 && successfulFiles < totalFiles) {
            message = `正在扫描代码文件 (${successfulFiles}/${totalFiles})`;
            step = 0;
          }
          // 步骤1: 创建知识库(文件全部扫描完成,但还没开始数据模型分析)
          else if (totalFiles > 0 && successfulFiles === totalFiles && analysisTotal === 0) {
            message = "正在创建知识库...";
            step = 1;
          }
          // 步骤2: 分析数据模型
          else if (analysisTotal > 0 && analysisSuccess < analysisTotal) {
            message = `正在分析数据模型 (${analysisSuccess}/${analysisTotal} 文件, ${analysisProgress}%)`;
            step = 2;
          }
          // 步骤3: 生成文档/文件树
          else {
            message = "正在生成文档结构和文件树...";
            step = 3;
          }

          // 保存带有当前步骤的信息,方便下面的进度条使用
          setTaskStatus({
            ...task,
            current_step: step,
            progress_percentage: step === 2 ? analysisProgress : undefined,
          });

          setProgressMessage(message);
          console.log("[FileExplorer] 进度消息:", message);
        } else if (task.status === "pending") {
          setProgressMessage("任务等待开始...");
        } else if (task.status === "completed") {
          console.log("[FileExplorer] 任务已完成");
        } else if (task.status === "failed") {
          setProgressMessage("分析任务失败, 请检查后台日志");
        }
      } catch (err) {
        console.error("[FileExplorer] 检查任务状态失败:", err);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, [taskId, error]);

  // 如果正在加载
  if (isLoading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
          <span className="text-sm">Loading files...</span>
        </div>
      </div>
    );
  }

  // 如果有错误
  if (error) {
    return (
        <div className="px-4 py-3 space-y-3">
          <div className="flex items-center space-x-3">
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent animate-spin rounded-full"/>
            <span className="text-gray-700 font-medium text-sm">文件树生成中</span>
          </div>

          {/* 进度条 */}
          {taskStatus?.current_step !== undefined && (
            <div className="pl-8 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">
                  步骤 {taskStatus.current_step + 1}/4
                </span>
                <span className="text-blue-600 font-medium">
                  {Math.round(((taskStatus.current_step + 1) / 4) * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                  style={{
                    width: `${((taskStatus.current_step + 1) / 4) * 100}%`,
                  }}
                />
              </div>
            </div>
          )}

          {/* 详细进度信息 */}
          <div className="pl-8 space-y-1">
            <p className="text-xs text-gray-600 font-medium">{progressMessage}</p>
            {taskStatus?.current_step === 2 && taskStatus?.progress_percentage !== undefined && (
              <p className="text-xs text-blue-600">
                文件分析: {taskStatus.progress_percentage}%
              </p>
            )}
          </div>
        </div>
    );
  }

  // 如果没有文件树数据，显示静态数据（用于my-awesome-project）
  const treeToRender = fileTree || mockFileTree;

  // 安全检查
  if (!treeToRender) {
    return (
      <div className="p-4">
        <div className="text-gray-500 text-sm py-4">No file tree available</div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-1">
      {/* 渲染文件树 */}
      {treeToRender.children &&
      Array.isArray(treeToRender.children) &&
      treeToRender.children.length > 0 ? (
        treeToRender.children.map((child) => (
          <FileTreeNode
            key={child.path}
            node={child}
            selectedFile={selectedFile}
            onFileSelect={onFileSelect}
            highlightedFile={highlightedFile}
            expandedPaths={expandedPaths}
            completedFiles={completedFiles}
            pendingFiles={pendingFiles}
          />
        ))
      ) : (
        <div className="text-gray-500 text-sm py-4">No files found</div>
      )}

      {/* 如果使用静态数据，显示根级文件 */}
      {!fileTree && (
        <div className="pt-2 border-t border-gray-200 mt-4">
          {[
            { name: "README.md", path: "README.md" },
            { name: "requirements.txt", path: "requirements.txt" },
            { name: ".env.example", path: ".env.example" },
          ].map((file) => (
            <Button
              key={file.path}
              variant="ghost"
              className={`
                w-full justify-start px-2 py-1 h-auto text-sm
                ${
                  selectedFile === file.path
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-700 hover:bg-gray-100"
                }
              `}
              onClick={() => onFileSelect(file.path)}
            >
              <File className="h-4 w-4 mr-2 text-gray-500" />
              <span className="truncate">{file.name}</span>
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
