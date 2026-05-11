"""应用核心配置 - 支持环境变量注入"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # JWT 密钥
    SECRET_KEY: str = "change_this_to_a_random_secret_key_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 天

    # 和风天气（全局默认，用户也可各自配置）
    QWEATHER_API_KEY: str = ""

    # 服务
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
