"""应用核心配置 - 支持环境变量注入"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # 和风天气
    QWEATHER_API_KEY: str = ""

    # 服务
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
