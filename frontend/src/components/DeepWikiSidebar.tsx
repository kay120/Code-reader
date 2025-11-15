import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ChevronDown,
  ChevronRight,
  BarChart3,
  Network,
  Layers,
  FileText,
  Loader2,
  MessageCircle,
} from "lucide-react";
import { Button } from "./ui/button";
import { api } from "../services/api";
import { useProject } from "../contexts/ProjectContext";

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  taskId?: number | null;
}

interface MarkdownSection {
  id: string;
  title: string;
  level: number;
  children?: MarkdownSection[];
}

// 解析markdown内容，提取标题结构
const parseMarkdownHeadings = (content: string): MarkdownSection[] => {
  console.log("Parsing markdown headings:", content);
  const lines = content.split("\n");
  console.log("Lines:", lines);
  const sections: MarkdownSection[] = [];
  const stack: MarkdownSection[] = [];
  let inCodeBlock = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmedLine = line.trim();

    // 检查是否在代码块中
    if (trimmedLine.startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      continue;
    }

    // 如果在代码块中，跳过这一行
    if (inCodeBlock) {
      continue;
    }
    console.log("Line:", line);
    // 更严格的标题匹配：确保 # 后面有空格，且不在行首有其他字符
    const h1Match = line.match(/^# (.+)/);
    const h2Match = line.match(/^## (.+)/);

    if (h1Match) {
      const title = h1Match[1].trim();
      // 过滤掉一些明显不是标题的内容
      if (isValidTitle(title)) {
        const id = generateSectionId(title);

        const section: MarkdownSection = {
          id,
          title,
          level: 1,
          children: [],
        };

        sections.push(section);
        stack.length = 0;
        stack.push(section);
      }
    } else if (h2Match && stack.length > 0) {
      const title = h2Match[1].trim();

      if (isValidTitle(title)) {
        const id = generateSectionId(title);

        const section: MarkdownSection = {
          id,
          title,
          level: 2,
        };

        const parent = stack[stack.length - 1];
        if (parent && parent.children) {
          parent.children.push(section);
        }
      }
    }
  }

  return sections;
};

// 验证是否是有效的标题
const isValidTitle = (title: string): boolean => {
  // 过滤掉空标题
  if (!title || title.trim().length === 0) {
    return false;
  }

  // 过滤掉只包含特殊字符的标题
  if (/^[#\-=\*\s]+$/.test(title)) {
    return false;
  }

  // 过滤掉看起来像代码或URL的内容
  if (
    title.includes("://") ||
    title.includes("```") ||
    title.startsWith("http")
  ) {
    return false;
  }

  // 过滤掉过长的标题（可能是误识别的内容）
  if (title.length > 100) {
    return false;
  }

  return true;
};

// 生成标题ID - 必须与 DeepWikiMainContent.tsx 中的逻辑完全一致
const generateSectionId = (title: string): string => {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5\s-]/g, "") // 保留连字符
    .replace(/\s+/g, "-")
    .replace(/^-+|-+$/g, ""); // 移除开头和结尾的连字符
};

export function Sidebar({
  activeSection,
  onSectionChange,
  taskId,
}: SidebarProps) {
  const navigate = useNavigate();
  const { currentRepository } = useProject();
  const [markdownSections, setMarkdownSections] = useState<MarkdownSection[]>(
    []
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set()
  );
  const [taskStatus, setTaskStatus] = useState<any>(null);
  const [progressMessage, setProgressMessage] = useState<string>("正在生成中...");

  // 加载README文档
  const loadReadmeContent = async (taskId: number) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log("Loading README for task:", taskId);
      const response = await api.getTaskReadmeByTaskId(taskId);

      if (response.status === "success" && response.readme) {
        const sections = parseMarkdownHeadings(response.readme.content);
        setMarkdownSections(sections);
        console.log("Parsed markdown sections:", sections);
      } else {
        setError("未找到README文档");
        setMarkdownSections([]);
      }
    } catch (err) {
      console.error("Error loading README:", err);
      setError("加载README文档失败");
      setMarkdownSections([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 检查任务状态并更新进度消息
  const checkTaskStatus = async (taskId: number) => {
    try {
      console.log('[DeepWikiSidebar] 检查任务状态, taskId:', taskId);

      // 添加超时控制
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000); // 8秒超时

      const response = await fetch(
        `http://localhost:8000/api/repository/analysis-tasks/${taskId}`,
        { signal: controller.abort }
      );

      clearTimeout(timeoutId);

      if (response.ok) {
        const result = await response.json();
        console.log('[DeepWikiSidebar] API响应:', result);

        // API返回的是任务列表,需要提取第一个任务
        const data = result.tasks && result.tasks.length > 0 ? result.tasks[0] : null;
        console.log('[DeepWikiSidebar] 任务状态:', data);
        setTaskStatus(data);

        // 根据任务状态生成进度消息
        if (data && data.status === "running") {
          // 根据文件进度和task_index判断当前步骤
          const successfulFiles = data.successful_files || 0;
          const totalFiles = data.total_files || 0;

          let step = 0;
          let message = "正在扫描代码文件...";

          if (successfulFiles === totalFiles && totalFiles > 0) {
            // 文件扫描完成
            if (data.task_index) {
              step = 2; // 有索引说明知识库已创建,在分析数据模型
              message = `正在分析数据模型 (${successfulFiles}/${totalFiles})`;
            } else {
              step = 1; // 正在创建知识库
              message = "正在创建知识库...";
            }
          } else if (successfulFiles > 0) {
            // 正在扫描文件
            step = 0;
            message = `正在扫描代码文件 (${successfulFiles}/${totalFiles})`;
          }

          // 更新taskStatus,添加current_step字段
          setTaskStatus({ ...data, current_step: step });

          // 如果在步骤3(生成文档),尝试获取deepwiki进度
          if (step === 3 && data.deepwiki_task_id) {
            try {
              const deepwikiResponse = await fetch(
                `http://localhost:8001/api/analyze/local/${data.deepwiki_task_id}/status`
              );
              if (deepwikiResponse.ok) {
                const deepwikiData = await deepwikiResponse.json();
                if (deepwikiData.progress !== undefined) {
                  message = `${deepwikiData.current_stage || "正在生成文档"} (${deepwikiData.progress}%)`;
                }
              }
            } catch (e) {
              console.error("获取deepwiki进度失败:", e);
            }
          }

          setProgressMessage(message);
          console.log('[DeepWikiSidebar] 进度消息:', message);
        } else if (data.status === "pending") {
          setProgressMessage("任务等待中...");
        } else if (data.status === "completed") {
          console.log('[DeepWikiSidebar] 任务已完成');
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.warn('[DeepWikiSidebar] 请求超时');
      } else {
        console.error("[DeepWikiSidebar] 检查任务状态失败:", err);
      }
    }
  };

  // 当taskId改变时加载README
  useEffect(() => {
    if (taskId) {
      loadReadmeContent(taskId);
      checkTaskStatus(taskId);

      // 如果任务还在进行中,每5秒检查一次状态
      const interval = setInterval(() => {
        checkTaskStatus(taskId);
      }, 5000);

      return () => clearInterval(interval);
    } else {
      setMarkdownSections([]);
    }
  }, [taskId]);

  // 切换展开状态
  const toggleExpanded = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  // 渲染markdown导航项
  const renderMarkdownSection = (section: MarkdownSection) => {
    const isExpanded = expandedSections.has(section.id);
    const hasChildren = section.children && section.children.length > 0;

    return (
      <div key={section.id} className="space-y-1">
        <Button
          variant="ghost"
          className={`
            w-full justify-start px-2 py-1 h-auto transition-all duration-100
            ${
              activeSection === section.id
                ? "bg-blue-100 text-blue-700"
                : "text-gray-700 hover:bg-gray-100"
            }
          `}
          onClick={() => {
            // 立即调用，不使用任何延迟
            onSectionChange(section.id);
            if (hasChildren) {
              toggleExpanded(section.id);
            }
          }}
        >
          <FileText className="h-4 w-4 mr-2" />
          <span className="text-sm flex-1 text-left">{section.title}</span>
          {hasChildren &&
            (isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            ))}
        </Button>

        {isExpanded && hasChildren && (
          <div className="ml-6 space-y-1">
            {section.children!.map((child) => (
              <Button
                key={child.id}
                variant="ghost"
                className={`
                  w-full justify-start px-2 py-1 h-auto text-sm transition-all duration-100
                  ${
                    activeSection === child.id
                      ? "bg-blue-50 text-blue-600"
                      : "text-gray-600 hover:bg-gray-50"
                  }
                `}
                onClick={() => {
                  // 立即调用，提供最快响应
                  onSectionChange(child.id);
                }}
              >
                {child.title}
              </Button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <nav className="p-4 space-y-2">
      {/* 项目概览 - 固定显示 */}
      <div className="space-y-1">
        <Button
          variant="ghost"
          className={`
            w-full justify-start px-2 py-1 h-auto transition-all duration-100
            ${
              activeSection === "overview"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-700 hover:bg-gray-100"
            }
          `}
          onClick={() => {
            // 立即响应，不使用任何延迟
            onSectionChange("overview");
          }}
        >
          <BarChart3 className="h-4 w-4 mr-2" />
          <span className="text-sm">项目概览</span>
        </Button>
      </div>

      {/* 分隔线 */}
      {markdownSections.length > 0 && (
        <div className="border-t border-gray-200 my-3"></div>
      )}

      {/* 加载状态 */}
      {isLoading && (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
          <span className="ml-2 text-sm text-gray-500">加载文档中...</span>
        </div>
      )}

      {/* 错误状态 - 正在生成中 */}
      {error && (
        <div className="space-y-3">
          <div className="px-2 py-2 space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent animate-spin rounded-full"/>
              <span className="text-gray-700 font-medium text-sm">文档生成中</span>
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
                  文件分析进度: {taskStatus.progress_percentage}%
                </p>
              )}
            </div>
          </div>
          <Button
            variant="outline"
            className="w-full justify-start px-3 py-2 h-auto text-blue-600 border-blue-200 hover:bg-blue-50"
            onClick={() => {
              const chatUrl = currentRepository?.claude_session_id
                ? `/chat/${currentRepository.claude_session_id}`
                : '/chat';
              navigate(chatUrl);
            }}
          >
            <MessageCircle className="h-4 w-4 mr-2" />
            <span className="text-sm">前往 AI 助手</span>
          </Button>
        </div>
      )}

      {/* Markdown导航 */}
      {markdownSections.map(renderMarkdownSection)}
    </nav>
  );
}
