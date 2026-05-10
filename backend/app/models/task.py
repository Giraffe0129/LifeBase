"""任务 / 当前任务 数据模型"""
import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="任务标题")
    description: Mapped[str] = mapped_column(Text, nullable=True, default="", comment="任务描述")
    completed: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否完成")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级: 0=普通 1=重要 2=紧急")
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
            "id": self.id,
            "title": self.title,
            "description": self.description or "",
            "completed": self.completed,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
