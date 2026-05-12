"""任务 / 当前任务 数据模型 - 支持拖拽排序 + 子任务"""
import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户")
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True, default=None, comment="父任务ID（子任务专用）")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="任务标题")
    description: Mapped[str] = mapped_column(Text, nullable=True, default="", comment="任务描述")
    completed: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否完成")
    priority: Mapped[int] = mapped_column(Integer, default=0, comment="优先级: 0=普通 1=重要 2=紧急")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="拖拽排序序号")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        comment="更新时间",
    )

    user = relationship("User", backref="tasks")
    parent = relationship("Task", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "parent_id": self.parent_id,
            "title": self.title,
            "description": self.description or "",
            "completed": self.completed,
            "priority": self.priority,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
