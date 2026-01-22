from __future__ import annotations
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 加载 .env 文件
load_dotenv()

class Settings(BaseSettings):
    """
    项目全局配置类
    Project Global Configuration
    """
    # OpenAI API 密钥 (必须配置)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # OpenAI 模型名称
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
    
    # Flask/Starlette 会话密钥 (用于 SessionMiddleware)
    session_secret: str = os.getenv("SESSION_SECRET", "change-me-random-string")
    
    # 数据库连接 URL
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # 测试账号 (仅开发环境)
    test_user_enabled: bool = os.getenv("TEST_USER_ENABLED", "true").lower() in {"1", "true", "yes"}
    test_user_email: str = os.getenv("TEST_USER_EMAIL", "test@example.com")
    test_user_password: str = os.getenv("TEST_USER_PASSWORD", "test123456")

settings = Settings()
