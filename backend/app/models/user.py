"""用户模型 - 支持多用户隔离和 API Key 配置"""
import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="用户名")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    # 用户自己的 API Key 配置
    qweather_api_key: Mapped[str] = mapped_column(
        String(100), nullable=True, default="", comment="用户自己的和风天气 API Key"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, comment="注册时间"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "has_qweather_key": bool(self.qweather_api_key),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
