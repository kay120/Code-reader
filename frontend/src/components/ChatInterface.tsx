import React, { useState, useRef, useEffect } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Textarea } from "./ui/textarea";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { ScrollArea } from "./ui/scroll-area";
import {
  Send,
  Bot,
  User,
  Sparkles,
  FileCode,
  Database,
  GitBranch,
  MessageSquare,
  Lightbulb,
  Code,
  Brain,
  ChevronLeft,
  Copy,
  Check,
  ArrowUp,
  Wrench,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { chatApi } from "../services/chat-api";
import { api } from "../services/api";
import { useProject } from "../contexts/ProjectContext";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isTyping?: boolean;
  toolUse?: {
    toolName: string;
    toolInput: any;
  };
}

interface ChatInterfaceProps {
  onBack: () => void;
  currentVersionId: string;
  sessionId: string;
}

const suggestedQuestions = [
  {
    icon: FileCode,
    text: "这个项目的主要架构是什么？",
    category: "架构分析",
  },
  {
    icon: Database,
    text: "项目中使用了哪些数据库技术？",
    category: "技术栈",
  },
  {
    icon: GitBranch,
    text: "代码的依赖关系如何？",
    category: "依赖分析",
  },
  {
    icon: Code,
    text: "有哪些可以优化的地方？",
    category: "代码优化",
  },
  {
    icon: Brain,
    text: "这个项目适合新手学习吗？",
    category: "学习建议",
  },
  {
    icon: Lightbulb,
    text: "如何快速上手这个项目？",
    category: "入门指南",
  },
];

const mockResponses = [
  `根据我对您项目的分析，这是一个使用React + TypeScript构建的现代化前端应用。项目采用了模块化的组件设计，具有良好的可维护性。

**主要特点：**
• 使用了Tailwind CSS进行样式管理
• 采用了shadcn/ui组件库
• 项目结构清晰，分离了业务逻辑和UI组件

**架构模式：**
- 单页应用(SPA)架构
- 组件化开发模式
- 状态提升和属性下传的数据流

这种架构设计既保证了代码的可维护性，又提供了良好的用户体验。`,

  `从代码分析来看，这个项目主要使用了以下技术栈：

**前端技术：**
• React 18+ (函数式组件 + Hooks)
• TypeScript (类型安全)
• Tailwind CSS (原子化CSS)
• Lucide React (图标库)

**构建工具：**
• Vite (现代化构建工具)
• ESLint + Prettier (代码规范)

**UI组件：**
• shadcn/ui (现代化组件库)
• Radix UI (无障碍组件基础)

目前没有发现数据库相关的技术栈，这是一个纯前端项目。如果需要数据持久化，建议考虑集成后端API或使用浏览器本地存储。`,

  `项目的依赖关系分析如下：

**核心依赖：**
• React生态系统组件相互依赖
• UI组件之间存在层级关系
• 工具函数模块被广泛引用

**组件依赖图：**
\`\`\`
App.tsx (根组件)
├── TopNavigation
├── UploadPage
├── AnalysisProgress  
├── DeepWikiInterface
├── PersonalSpace
└── ChatInterface
\`\`\`

**建议：**
依赖关系整体健康，没有循环依赖问题。组件间耦合度适中，便于维护和扩展。`,

  `基于代码分析，我发现以下可以优化的地方：

**性能优化：**
• 可以使用React.memo()优化组件重渲染
• 大列表可以考虑虚拟滚动
• 图片懒加载可以提升页面加载速度

**代码结构：**
• 一些组件过于复杂，建议拆分
• 状态管理可以考虑使用Context或状态管理库
• 添加单元测试覆盖

**用户体验：**
• 添加加载状态指示器
• 错误边界处理
• 键盘导航支持

**代码示例：**
\`\`\`typescript
// 使用React.memo优化性能
export const OptimizedComponent = React.memo(({ data }) => {
  return <div>{data}</div>;
});
\`\`\``,

  `这个项目非常适合新手学习！原因如下：

**学习友好性：**
• 使用了现代React最佳实践
• 代码结构清晰，注释完善
• 采用了TypeScript，有助于理解类型系统

**技术覆盖面：**
• 涵盖了现代前端开发的核心技术
• 组件设计模式值得学习
• 状态管理和事件处理示例丰富

**推荐学习顺序：**
1. 从基础组件开始理解
2. 学习状态管理模式
3. 理解组件间通信
4. 掌握TypeScript类型定义

这个项目可以作为很好的React学习案例。`,

  `快速上手这个项目的建议：

**第一步：环境搭建**
\`\`\`bash
npm install
npm run dev
\`\`\`

**第二步：理解项目结构**
• \`/components\` - 所有React组件
• \`/styles\` - 全局样式文件
• \`App.tsx\` - 应用主入口

**第三步：从简单页面开始**
1. 先看UploadPage组件，理解基础交互
2. 研究UI组件的使用方法
3. 理解状态管理逻辑

**第四步：尝试修改**
• 调整样式看效果
• 添加新的功能按钮
• 修改文案内容

**注意事项：**
确保Node.js版本 >= 16，推荐使用最新的LTS版本。`,
];

// Markdown 渲染组件
const MessageContent = ({ content }: { content: string }) => {
  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // @ts-ignore - 自定义样式组件
          h1: ({ node, ...props }) => (
            <h1 className="text-xl font-bold text-gray-900 mt-4 mb-2" {...props} />
          ),
          // @ts-ignore
          h2: ({ node, ...props }) => (
            <h2 className="text-lg font-bold text-gray-900 mt-3 mb-2" {...props} />
          ),
          // @ts-ignore
          h3: ({ node, ...props }) => (
            <h3 className="text-base font-semibold text-gray-900 mt-3 mb-2" {...props} />
          ),
          // @ts-ignore
          h4: ({ node, ...props }) => (
            <h4 className="text-sm font-semibold text-gray-900 mt-2 mb-1" {...props} />
          ),
          // @ts-ignore
          p: ({ node, ...props }) => (
            <p className="text-gray-700 leading-relaxed my-2" {...props} />
          ),
          // @ts-ignore
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside space-y-1 my-2 text-gray-700" {...props} />
          ),
          // @ts-ignore
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside space-y-1 my-2 text-gray-700" {...props} />
          ),
          // @ts-ignore
          li: ({ node, ...props }) => (
            <li className="text-gray-700" {...props} />
          ),
          // @ts-ignore
          code: ({ node, inline, className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || "");
            // 判断是否为内联代码：
            // 1. 如果 inline 参数存在且为 true，则为内联代码
            // 2. 如果没有 className（没有语言标记），且内容较短，则视为内联代码
            const codeContent = String(children).replace(/\n$/, '');
            const isInline = inline === true || (!className && !codeContent.includes('\n') && codeContent.length < 100);

            return !isInline ? (
              <div className="my-3 rounded-lg overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2 bg-gray-800 text-gray-300 text-sm">
                  <span className="flex items-center space-x-2">
                    <Code className="h-4 w-4" />
                    <span>{match ? match[1] : "code"}</span>
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-gray-400 hover:text-white"
                    onClick={() => navigator.clipboard.writeText(codeContent)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
                <code className={`${className} block p-4 text-sm bg-gray-900 text-gray-100 overflow-x-auto`} {...props}>
                  {children}
                </code>
              </div>
            ) : (
              <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                {children}
              </code>
            );
          },
          // @ts-ignore
          pre: ({ node, ...props }) => (
            <pre className="my-0" {...props} />
          ),
          // @ts-ignore
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-3 text-gray-700 italic bg-blue-50" {...props} />
          ),
          // @ts-ignore
          a: ({ node, ...props }) => (
            <a className="text-blue-600 hover:text-blue-800 underline" {...props} />
          ),
          // @ts-ignore
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-3">
              <table className="min-w-full divide-y divide-gray-300 border border-gray-300" {...props} />
            </div>
          ),
          // @ts-ignore
          thead: ({ node, ...props }) => (
            <thead className="bg-gray-50" {...props} />
          ),
          // @ts-ignore
          th: ({ node, ...props }) => (
            <th className="px-3 py-2 text-left text-sm font-semibold text-gray-900 border border-gray-300" {...props} />
          ),
          // @ts-ignore
          td: ({ node, ...props }) => (
            <td className="px-3 py-2 text-sm text-gray-700 border border-gray-300" {...props} />
          ),
          // @ts-ignore
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-gray-900" {...props} />
          ),
          // @ts-ignore
          em: ({ node, ...props }) => (
            <em className="italic text-gray-800" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default function ChatInterface({
  onBack,
  currentVersionId,
  sessionId,
}: ChatInterfaceProps) {
  const { currentRepository } = useProject();

  // 调试日志
  console.log("ChatInterface - currentRepository:", currentRepository);
  console.log("ChatInterface - sessionId:", sessionId);

  // ✅ 从 localStorage 加载历史消息
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem(`chat_history_${sessionId}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        // 恢复 Date 对象
        return parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
    return [];
  });

  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionValid, setSessionValid] = useState<boolean | null>(null); // null = 未检查, true = 有效, false = 无效
  const [isInitializing, setIsInitializing] = useState(false); // 是否正在初始化 session
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string>(
    () => crypto.randomUUID()
  );
  // 工具调用折叠状态：key 是消息组的第一个消息ID，value 是是否展开
  const [toolCallsExpanded, setToolCallsExpanded] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ✅ 保存历史消息到 localStorage
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem(`chat_history_${sessionId}`, JSON.stringify(messages));
      } catch (error) {
        console.error('Failed to save chat history:', error);
      }
    }
  }, [messages, sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 将连续的工具调用消息分组
  const groupMessages = (messages: ChatMessage[]) => {
    const groups: Array<{ type: 'single' | 'toolGroup', messages: ChatMessage[], id: string }> = [];
    let currentToolGroup: ChatMessage[] = [];

    messages.forEach((msg, index) => {
      if (msg.toolUse) {
        // 如果是工具调用消息，添加到当前组
        currentToolGroup.push(msg);
      } else {
        // 如果不是工具调用消息
        if (currentToolGroup.length > 0) {
          // 先保存之前的工具调用组
          groups.push({
            type: 'toolGroup',
            messages: currentToolGroup,
            id: currentToolGroup[0].id
          });
          currentToolGroup = [];
        }
        // 添加当前消息
        groups.push({
          type: 'single',
          messages: [msg],
          id: msg.id
        });
      }
    });

    // 处理最后一组工具调用
    if (currentToolGroup.length > 0) {
      groups.push({
        type: 'toolGroup',
        messages: currentToolGroup,
        id: currentToolGroup[0].id
      });
    }

    return groups;
  };

  const toggleToolGroup = (groupId: string) => {
    setToolCallsExpanded(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }));
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    // 创建AI响应消息（初始为空）
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    // setMessages((prev) => [...prev, assistantMessage]);

    try {
      // 使用从URL传递的sessionId
      console.log("使用sessionId:", sessionId);

      // 只在第一次发送消息时检查 session 是否存在
      if (sessionValid === null) {
        const testResponse = await fetch(`/code_chat/api/chat/${sessionId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: "test",
            conversation_id: conversationId
          })
        });

        if (!testResponse.ok) {
          const errorData = await testResponse.json();
          if (errorData.detail === "Session not found") {
            // Session 不存在，尝试自动初始化
            if (!currentRepository?.id) {
              setSessionValid(false);
              setMessages((prev) => [...prev, {
                id: assistantMessageId,
                role: "assistant",
                content: "❌ **无法初始化 AI 问答**\n\n无法获取当前项目信息。请返回项目列表重新进入。",
                timestamp: new Date(),
              }]);
              setIsLoading(false);
              return;
            }

            // 显示初始化提示
            const initMessageId = (Date.now() + 2).toString();
            setMessages((prev) => [...prev, {
              id: initMessageId,
              role: "assistant",
              content: "🔄 **正在初始化 AI 问答服务...**\n\n首次使用需要上传代码库到 AI 服务，请稍候...",
              timestamp: new Date(),
            }]);

            setIsInitializing(true);

            try {
              // 调用后端 API 初始化 session
              const result = await api.initClaudeSession(currentRepository.id);

              if (result.status === 'success' && result.session_id) {
                // 初始化成功，更新消息
                setMessages((prev) => prev.map(msg =>
                  msg.id === initMessageId
                    ? { ...msg, content: "✅ **AI 问答服务初始化成功！**\n\n现在可以开始提问了。" }
                    : msg
                ));
                setSessionValid(true);
                setIsInitializing(false);

                // ✅ 重要：使用新的 session_id 发送消息
                console.log(`🔄 Session 初始化成功，新 session_id: ${result.session_id}`);

                // 使用新的 session_id 重新发送消息
                await chatApi.sendMessage(
                  result.session_id,  // 使用新的 session_id
                  content.trim(),
                  conversationId,
                  (event: string, data: any) => {
                    console.log("event", event);
                    // 处理不同的SSE事件
                    switch (event) {
                        case "text_delta":
                          console.log("text_delta-event", data);
                          if (data && data.delta) {
                            console.log("data", data);
                            const newMessage: ChatMessage = {
                              id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                              role: "assistant",
                              content: data.delta,
                              timestamp: new Date(),
                            };
                            setMessages((prev) => [...prev, newMessage]);
                          }
                          break;
                        case "tool_use":
                          console.log("tool_use-event", data);
                          if (data && data.tool_name) {
                            const toolMessage: ChatMessage = {
                              id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                              role: "assistant",
                              content: "",
                              timestamp: new Date(),
                              toolUse: {
                                toolName: data.tool_name,
                                toolInput: data.tool_input,
                              },
                            };
                            setMessages((prev) => [...prev, toolMessage]);
                          }
                          break;
                        case "message_stop":
                          console.log("message_stop-event", data);
                          setIsLoading(false);
                          break;
                        case "error":
                          console.error("error-event", data);
                          const errorMessage: ChatMessage = {
                            id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                            role: "assistant",
                            content: `❌ **错误**\n\n${data.error_message || "未知错误"}`,
                            timestamp: new Date(),
                          };
                          setMessages((prev) => [...prev, errorMessage]);
                          setIsLoading(false);
                          break;
                    }
                  }
                );

                // 已经发送消息，直接返回
                return;
              } else {
                throw new Error(result.message || '初始化失败');
              }
            } catch (error: any) {
              setMessages((prev) => prev.map(msg =>
                msg.id === initMessageId
                  ? {
                      ...msg,
                      content: `❌ **AI 问答服务初始化失败**\n\n${error.message || error}\n\n请稍后重试或联系管理员。`
                    }
                  : msg
              ));
              setSessionValid(false);
              setIsInitializing(false);
              setIsLoading(false);
              return;
            }
          }
        } else {
          // Session 有效，标记为已验证
          setSessionValid(true);
        }
      }

      // 如果之前检查过且无效，直接返回
      if (sessionValid === false) {
        setMessages((prev) => [...prev, {
          id: assistantMessageId,
          role: "assistant",
          content: "❌ **AI 问答服务未初始化**\n\n请参考上面的提示解决此问题。",
          timestamp: new Date(),
        }]);
        setIsLoading(false);
        return;
      }
      
      // 调用真实的API
      await chatApi.sendMessage(
        sessionId,
        content.trim(),
        conversationId,
        (event: string, data: any) => {
          console.log("event", event);
          // 处理不同的SSE事件
          switch (event) {
              case "text_delta":
                console.log("text_delta-event", data);
                // ✅ 收到第一个文本增量时，取消 loading 状态
                setIsLoading(false);
                if (data && data.delta) {
                  console.log("data", data);
                  // ✅ 累积文本到同一个消息，而不是每次都创建新消息
                  setMessages((prev) => {
                    const lastMsg = prev[prev.length - 1];
                    // 如果最后一条消息是 assistant 且 id 匹配，则累积文本
                    if (lastMsg && lastMsg.id === assistantMessageId && lastMsg.role === "assistant") {
                      return prev.map((msg, idx) =>
                        idx === prev.length - 1
                          ? { ...msg, content: msg.content + data.delta }
                          : msg
                      );
                    } else {
                      // 否则创建新消息
                      return [...prev, {
                        id: assistantMessageId,
                        role: "assistant",
                        content: data.delta,
                        timestamp: new Date(),
                      }];
                    }
                  });
                }
                break;

            case "tool_use":
              // 工具使用事件
              if (data && data.tool_name) {
                console.log("工具调用:", data);
                const toolMessage: ChatMessage = {
                  id: `tool_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                  role: "assistant",
                  content: "",
                  timestamp: new Date(),
                  toolUse: {
                    toolName: data.tool_name,
                    toolInput: data.tool_input,
                  },
                };
                setMessages((prev) => [...prev, toolMessage]);
              }
              break;

            case "done":
              // 消息发送完成
              console.log("消息发送完成", data);
              break;
              

            case "error":
              // 错误处理
              console.error("聊天错误:", data);
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? {
                        ...msg,
                        content:
                          msg.content ||
                          `抱歉，发生了错误：${data.message || "未知错误"}`,
                      }
                    : msg
                )
              );
              break;

            default:
              console.log("未处理的事件:", event, data);
          }
        }
      );
    } catch (error) {
      console.error("发送消息失败:", error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content:
                  msg.content ||
                  `抱歉，发送消息失败：${error instanceof Error ? error.message : "网络错误"}`,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const copyToClipboard = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="flex-shrink-0 p-4 bg-white/80 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-none mx-auto px-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={onBack} className="p-2">
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">AI 代码助手</h1>
                <p className="text-sm text-gray-600">
                  基于项目 v{currentVersionId} 的智能问答
                </p>
              </div>
            </div>
          </div>

          <Badge variant="secondary" className="flex items-center space-x-1">
            <Sparkles className="h-3 w-3" />
            <span>本地AI模型</span>
          </Badge>
        </div>
      </div>

      {/* Chat Content */}
      <div className="flex-1 flex max-w-none mx-auto w-full px-8 py-6 space-x-8">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <Card className="flex-1 flex flex-col shadow-lg">
            {/* Messages Area */}
            <div className="flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                {messages.length === 0 ? (
                  /* Welcome Message */
                  <div className="h-full flex flex-col items-center justify-center p-12">
                    <div className="text-center space-y-6 max-w-2xl">
                      <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto">
                        <MessageSquare className="h-10 w-10 text-white" />
                      </div>
                      <div className="space-y-3">
                        <h3 className="text-2xl font-bold text-gray-900">
                          欢迎使用 AI 代码助手
                        </h3>
                        <p className="text-gray-600 leading-relaxed">
                          我已经深入分析了您的项目代码，可以回答关于架构设计、技术栈选择、依赖关系、优化建议等任何问题。让我们开始探索您的代码库吧！
                        </p>
                      </div>
                      <div className="flex items-center justify-center space-x-4 text-sm text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Brain className="h-4 w-4" />
                          <span>智能分析</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <FileCode className="h-4 w-4" />
                          <span>代码理解</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Lightbulb className="h-4 w-4" />
                          <span>优化建议</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Messages List */
                  <div className="p-8 space-y-8">
                    {groupMessages(messages).map((group) => {
                      // 如果是工具调用组
                      if (group.type === 'toolGroup') {
                        const isExpanded = toolCallsExpanded[group.id] || false;
                        return (
                          <div key={group.id} className="flex justify-start">
                            <div className="flex items-start space-x-4 max-w-[90%]">
                              {/* Avatar */}
                              <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-md bg-gradient-to-r from-amber-500 to-orange-600">
                                <Wrench className="h-5 w-5 text-white" />
                              </div>

                              {/* Tool Calls Group */}
                              <div className="group flex-1 text-left">
                                <div className="inline-block p-4 rounded-xl relative shadow-sm bg-amber-50 border border-amber-200 text-gray-900 rounded-bl-md">
                                  {/* Header with collapse button */}
                                  <div
                                    className="flex items-center justify-between cursor-pointer hover:bg-amber-100 -m-4 p-4 rounded-t-xl transition-colors"
                                    onClick={() => toggleToolGroup(group.id)}
                                  >
                                    <div className="flex items-center space-x-2 text-amber-700">
                                      <Wrench className="h-4 w-4" />
                                      <span className="font-semibold text-sm">
                                        工具调用 ({group.messages.length})
                                      </span>
                                    </div>
                                    {isExpanded ? (
                                      <ChevronDown className="h-4 w-4 text-amber-700" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4 text-amber-700" />
                                    )}
                                  </div>

                                  {/* Tool calls list (collapsible) */}
                                  {isExpanded && (
                                    <div className="mt-4 space-y-3">
                                      {group.messages.map((msg, idx) => (
                                        <div key={msg.id} className="p-3 bg-white rounded-lg border border-amber-200">
                                          <div className="text-sm font-medium text-amber-800 mb-2">
                                            {idx + 1}. {msg.toolUse?.toolName}
                                          </div>
                                          {msg.toolUse?.toolInput && Object.keys(msg.toolUse.toolInput).length > 0 && (
                                            <div>
                                              <div className="text-xs font-medium text-gray-600 mb-1">
                                                参数:
                                              </div>
                                              <pre className="text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">
                                                {JSON.stringify(msg.toolUse.toolInput, null, 2)}
                                              </pre>
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>

                                <div className="text-xs text-gray-500 mt-2 text-left">
                                  {formatTimestamp(group.messages[0].timestamp)}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      }

                      // 如果是单个消息
                      const message = group.messages[0];
                      return (
                      <div
                        key={message.id}
                        className={`flex ${
                          message.role === "user"
                            ? "justify-end"
                            : "justify-start"
                        }`}
                      >
                        <div
                          className={`flex items-start space-x-4 max-w-[90%] ${
                            message.role === "user"
                              ? "flex-row-reverse space-x-reverse"
                              : ""
                          }`}
                        >
                          {/* Avatar */}
                          <div
                            className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-md ${
                              message.role === "user"
                                ? "bg-blue-600"
                                : "bg-gradient-to-r from-blue-500 to-purple-600"
                            }`}
                          >
                            {message.role === "user" ? (
                              <User className="h-5 w-5 text-white" />
                            ) : (
                              <Bot className="h-5 w-5 text-white" />
                            )}
                          </div>

                          {/* Message Content */}
                          <div
                            className={`group flex-1 ${
                              message.role === "user"
                                ? "text-right"
                                : "text-left"
                            }`}
                          >
                            <div
                              className={`inline-block p-4 rounded-xl relative shadow-sm ${
                                message.role === "user"
                                  ? "bg-blue-600 text-white rounded-br-md"
                                  : message.toolUse
                                  ? "bg-amber-50 border border-amber-200 text-gray-900 rounded-bl-md"
                                  : "bg-white border border-gray-200 text-gray-900 rounded-bl-md"
                              }`}
                            >
                              {message.role === "user" ? (
                                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                                  {message.content}
                                </div>
                              ) : message.toolUse ? (
                                /* 工具调用显示 */
                                <div className="space-y-2">
                                  <div className="flex items-center space-x-2 text-amber-700">
                                    <Wrench className="h-4 w-4" />
                                    <span className="font-semibold text-sm">
                                      调用工具: {message.toolUse.toolName}
                                    </span>
                                  </div>
                                  {message.toolUse.toolInput && Object.keys(message.toolUse.toolInput).length > 0 && (
                                    <div className="mt-2 p-3 bg-white rounded-lg border border-amber-200">
                                      <div className="text-xs font-medium text-gray-600 mb-1">
                                        参数:
                                      </div>
                                      <pre className="text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">
                                        {JSON.stringify(
                                          message.toolUse.toolInput,
                                          null,
                                          2
                                        )}
                                      </pre>
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <MessageContent content={message.content} />
                              )}

                              {/* Copy button for assistant messages */}
                              {message.role === "assistant" && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="absolute top-2 right-2 h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-50 hover:bg-gray-100"
                                  onClick={() =>
                                    copyToClipboard(message.content, message.id)
                                  }
                                >
                                  {copiedMessageId === message.id ? (
                                    <Check className="h-3 w-3 text-green-600" />
                                  ) : (
                                    <Copy className="h-3 w-3 text-gray-600" />
                                  )}
                                </Button>
                              )}
                            </div>

                            <div
                              className={`text-xs text-gray-500 mt-2 ${
                                message.role === "user"
                                  ? "text-right"
                                  : "text-left"
                              }`}
                            >
                              {formatTimestamp(message.timestamp)}
                            </div>
                          </div>
                        </div>
                      </div>
                      );
                    })}

                    {/* Loading indicator */}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="flex items-start space-x-4 max-w-[90%]">
                          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-md">
                            <Bot className="h-5 w-5 text-white" />
                          </div>
                          <div className="bg-white border border-gray-200 rounded-xl rounded-bl-md p-4 shadow-sm">
                            <div className="flex items-center space-x-3">
                              <div className="flex space-x-1">
                                <div
                                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                  style={{ animationDelay: "0ms" }}
                                ></div>
                                <div
                                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                  style={{ animationDelay: "150ms" }}
                                ></div>
                                <div
                                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                  style={{ animationDelay: "300ms" }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-500">
                                AI正在分析思考...
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>
                )}
              </ScrollArea>
            </div>

            {/* Input Area */}
            <div className="p-6 border-t border-gray-200 bg-gray-50/50">
              <div className="flex space-x-4">
                <div className="flex-1 relative">
                  <Textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="询问关于代码库的任何问题... (Enter发送，Shift+Enter换行)"
                    className="resize-none bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500 text-base"
                    rows={4}
                    disabled={isLoading}
                  />
                </div>
                <Button
                  onClick={() => handleSendMessage(inputValue)}
                  disabled={!inputValue.trim() || isLoading}
                  className="self-end h-auto px-5 py-4"
                >
                  <ArrowUp className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar with Suggested Questions */}
        <div className="w-96 space-y-4 flex-shrink-0">
          <Card className="p-5 shadow-lg">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <Lightbulb className="h-5 w-5 text-yellow-500" />
              <span>推荐问题</span>
            </h3>

            <div className="space-y-3">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question.text)}
                  className="w-full p-4 text-left rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 group disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isLoading}
                >
                  <div className="flex items-start space-x-3">
                    <question.icon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5 group-hover:text-blue-700" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900 group-hover:text-blue-700 leading-relaxed">
                        {question.text}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {question.category}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </Card>

          <Card className="p-5 shadow-lg">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <Brain className="h-5 w-5 text-purple-500" />
              <span>AI 能力</span>
            </h3>

            <div className="space-y-4 text-sm">
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-blue-50">
                <FileCode className="h-4 w-4 text-blue-600" />
                <span className="text-blue-800 font-medium">代码架构分析</span>
              </div>
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-green-50">
                <Database className="h-4 w-4 text-green-600" />
                <span className="text-green-800 font-medium">技术栈识别</span>
              </div>
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-orange-50">
                <GitBranch className="h-4 w-4 text-orange-600" />
                <span className="text-orange-800 font-medium">
                  依赖关系梳理
                </span>
              </div>
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-purple-50">
                <Code className="h-4 w-4 text-purple-600" />
                <span className="text-purple-800 font-medium">
                  代码优化建议
                </span>
              </div>
            </div>

            <Separator className="my-4" />

            <div className="text-xs text-gray-500 space-y-1">
              <p className="flex items-center space-x-1">
                <Sparkles className="h-3 w-3" />
                <span>基于本地AI模型，确保代码安全</span>
              </p>
              <p className="text-gray-400">数据不出域，隐私有保障</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
