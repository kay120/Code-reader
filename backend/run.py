"""
启动脚本
"""

import uvicorn
from config import settings
import logging

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,  # 暂时禁用 reload 以避免问题
        log_level="info",
        workers=12,  # 使用12个worker进程,进一步降低请求阻塞概率
    )
