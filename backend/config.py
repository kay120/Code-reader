"""
配置文件
"""

import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 先清除可能存在的系统环境变量，确保只使用 .env 文件中的配置
env_keys_to_clear = [
    'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL', 'OPENAI_API_BASE',
    'LLM_MAX_CONCURRENT', 'LLM_BATCH_SIZE', 'LLM_REQUEST_TIMEOUT', 'LLM_RETRY_DELAY'
]
for key in env_keys_to_clear:
    os.environ.pop(key, None)

# 加载项目根目录的 .env 文件（Code-reader/.env）
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path, override=True)


class Settings:
    """应用配置类"""

    # 应用基本配置
    APP_NAME: str = "AI 代码库领航员 API"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))

    # 数据库配置
    DB_DIALECT: str = os.getenv("DB_DIALECT", "mysql+pymysql")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_NAME: str = os.getenv("DB_NAME", "code_analysis")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "123456")
    DB_PARAMS: str = os.getenv("DB_PARAMS", "charset=utf8mb4")
    DB_ECHO: bool = bool(int(os.getenv("DB_ECHO", 0)))
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 50))  # 进一步增加连接池大小
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", 50))  # 进一步增加溢出连接数
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", 3600))  # 连接回收时间(秒)

    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        # 对用户名和密码进行URL编码，处理特殊字符
        encoded_user = quote_plus(self.DB_USER)
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"{self.DB_DIALECT}://{encoded_user}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?{self.DB_PARAMS}"

    # GitHub API配置
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # OpenAI API配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # LLM 并行处理配置
    LLM_MAX_CONCURRENT: int = int(os.getenv("LLM_MAX_CONCURRENT", 1))  # 进一步降低并发数为1
    LLM_BATCH_SIZE: int = int(os.getenv("LLM_BATCH_SIZE", 5))  # 进一步降低批处理大小
    LLM_REQUEST_TIMEOUT: int = int(os.getenv("LLM_REQUEST_TIMEOUT", 120))
    LLM_RETRY_DELAY: int = int(os.getenv("LLM_RETRY_DELAY", 2))

    # 分析任务资源限制配置
    ANALYSIS_MAX_CONCURRENT_FILES: int = int(os.getenv("ANALYSIS_MAX_CONCURRENT_FILES", 1))  # 降低为1个文件
    ANALYSIS_SLEEP_BETWEEN_FILES: float = float(os.getenv("ANALYSIS_SLEEP_BETWEEN_FILES", 2.0))  # 增加延迟到2秒

    # RAG 服务配置
    RAG_BASE_URL: str = os.getenv("RAG_BASE_URL", "")
    RAG_BATCH_SIZE: int = int(os.getenv("RAG_BATCH_SIZE", 100))

    # README API 配置
    README_API_BASE_URL: str = os.getenv("README_API_BASE_URL", "http://127.0.0.1:8001")
    CLAUDE_CHAT_API_BASE_URL: str = os.getenv("CLAUDE_CHAT_API_BASE_URL", "http://127.0.0.1:8002")

    # 本地存储配置
    LOCAL_REPO_PATH: str = os.getenv("LOCAL_REPO_PATH", "./data/repos")
    RESULTS_PATH: str = os.getenv("RESULTS_PATH", "./data/results")
    VECTORSTORE_PATH: str = os.getenv("VECTORSTORE_PATH", "./data/vectorstores")


# 创建全局配置实例
settings = Settings()
