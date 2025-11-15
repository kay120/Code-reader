import { useState, useEffect } from "react";
import { Activity, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./ui/popover";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";

interface ServiceStatus {
  name: string;
  url: string;
  status: "healthy" | "unhealthy" | "checking" | "busy";
  responseTime?: number;
  error?: string;
  warning?: string;
}

const SERVICES = [
  {
    name: "Code-reader 后端",
    url: "http://localhost:8000/health",
    key: "backend",
    checkBusy: true, // 需要检查是否繁忙
  },
  {
    name: "本地 RAG 服务",
    url: "http://localhost:32421/health",
    key: "rag",
    checkBusy: false,
  },
  {
    name: "deepwiki 服务",
    url: "http://localhost:8001/health",
    key: "deepwiki",
    checkBusy: false,
  },
  {
    name: "claude-agent-sdk",
    url: "http://localhost:8003/",
    key: "claude",
    checkBusy: false,
  },
];

export default function ServiceHealthMonitor() {
  const [services, setServices] = useState<ServiceStatus[]>(
    SERVICES.map((s) => ({
      name: s.name,
      url: s.url,
      status: "checking" as const,
    }))
  );
  const [isOpen, setIsOpen] = useState(false);

  const checkServiceHealth = async (service: typeof SERVICES[0]) => {
    const startTime = Date.now();

    // 第一次尝试 - 20秒超时
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 20000); // 增加到20秒

      const response = await fetch(service.url, {
        method: "GET",
        signal: controller.signal,
        mode: 'cors',
        credentials: 'omit',
      });

      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;

      if (response.ok) {
        // 响应时间超过10秒,显示警告但仍标记为正常
        if (responseTime > 10000) {
          return {
            name: service.name,
            url: service.url,
            status: "healthy" as const,
            responseTime,
            warning: `响应较慢 (${Math.round(responseTime/1000)}s)`,
          };
        }

        return {
          name: service.name,
          url: service.url,
          status: "healthy" as const,
          responseTime,
        };
      } else {
        return {
          name: service.name,
          url: service.url,
          status: "unhealthy" as const,
          error: `HTTP ${response.status}`,
        };
      }
    } catch (error) {
      const responseTime = Date.now() - startTime;

      // 如果第一次超时,且是后端服务,尝试第二次(快速检查)
      if (error instanceof Error && error.name === 'AbortError' && service.checkBusy) {
        try {
          // 第二次尝试 - 5秒快速检查
          const controller2 = new AbortController();
          const timeoutId2 = setTimeout(() => controller2.abort(), 5000);

          const response2 = await fetch(service.url, {
            method: "GET",
            signal: controller2.signal,
            mode: 'cors',
            credentials: 'omit',
          });

          clearTimeout(timeoutId2);
          const responseTime2 = Date.now() - startTime;

          if (response2.ok) {
            // 第二次成功了,说明服务正常,只是第一次时比较忙
            return {
              name: service.name,
              url: service.url,
              status: "healthy" as const,
              responseTime: responseTime2,
              warning: "服务负载较高",
            };
          }
        } catch (retryError) {
          // 第二次也失败了,标记为繁忙
          return {
            name: service.name,
            url: service.url,
            status: "busy" as const,
            warning: "服务繁忙,正在处理分析任务",
            responseTime: undefined,
          };
        }
      }

      // 处理其他错误
      let errorMessage = "连接失败";

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = "请求超时 (>20s)";
        } else if (error.message.includes('Failed to fetch')) {
          errorMessage = "无法连接";
        } else {
          errorMessage = error.message;
        }
      }

      return {
        name: service.name,
        url: service.url,
        status: "unhealthy" as const,
        error: errorMessage,
        responseTime: responseTime > 20000 ? undefined : responseTime,
      };
    }
  };

  const checkAllServices = async () => {
    const results = await Promise.all(
      SERVICES.map((service) => checkServiceHealth(service))
    );
    setServices(results);
  };

  useEffect(() => {
    // 初始检查
    checkAllServices();

    // 每60秒检查一次(降低频率,减少后端负担)
    const interval = setInterval(checkAllServices, 60000);

    return () => clearInterval(interval);
  }, []);

  // 当打开面板时,立即刷新一次
  useEffect(() => {
    if (isOpen) {
      checkAllServices();
    }
  }, [isOpen]);

  const getOverallStatus = () => {
    const unhealthyCount = services.filter(
      (s) => s.status === "unhealthy"
    ).length;
    const checkingCount = services.filter(
      (s) => s.status === "checking"
    ).length;
    const busyCount = services.filter(
      (s) => s.status === "busy"
    ).length;

    if (checkingCount > 0) return "checking";
    if (unhealthyCount > 0) return "unhealthy";
    if (busyCount > 0) return "busy";
    return "healthy";
  };

  const getStatusIcon = (status: ServiceStatus["status"]) => {
    switch (status) {
      case "healthy":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "unhealthy":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "busy":
        return <Activity className="h-4 w-4 text-orange-600 animate-pulse" />;
      case "checking":
        return <AlertCircle className="h-4 w-4 text-yellow-600 animate-pulse" />;
    }
  };

  const getStatusBadge = (status: ServiceStatus["status"]) => {
    switch (status) {
      case "healthy":
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">正常</Badge>;
      case "unhealthy":
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">异常</Badge>;
      case "busy":
        return <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100">繁忙</Badge>;
      case "checking":
        return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">检查中</Badge>;
    }
  };

  const overallStatus = getOverallStatus();

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" className="relative">
          <Activity className="h-4 w-4 mr-2" />
          <span className="hidden md:inline">服务状态</span>
          {overallStatus === "unhealthy" && (
            <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full animate-pulse" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-sm">服务健康监控</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={checkAllServices}
              className="h-7 text-xs"
            >
              刷新
            </Button>
          </div>

          <div className="space-y-3">
            {services.map((service) => (
              <div
                key={service.name}
                className="flex items-start justify-between p-2 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-start space-x-2 flex-1">
                  {getStatusIcon(service.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {service.name}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {service.url}
                    </p>
                    {service.responseTime && (
                      <p className="text-xs text-muted-foreground">
                        响应时间: {service.responseTime}ms
                      </p>
                    )}
                    {service.error && (
                      <p className="text-xs text-red-600">{service.error}</p>
                    )}
                    {service.warning && (
                      <p className="text-xs text-orange-600">{service.warning}</p>
                    )}
                  </div>
                </div>
                <div className="ml-2">{getStatusBadge(service.status)}</div>
              </div>
            ))}
          </div>

          <div className="text-xs text-muted-foreground text-center pt-2 border-t">
            每60秒自动刷新
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

