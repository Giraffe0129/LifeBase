"""用户设置模型 - 支持功能开关等"""
import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True, comment="所属用户")
    # 功能开关
    weather_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="天气显示开关")
    # 扩展设置（JSON 存储）
    extras: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict, comment="扩展设置")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        comment="更新时间",
    )

    def to_dict(self):
        return {
            "weather_enabled": self.weather_enabled,
            "extras": self.extras or {},
        }
