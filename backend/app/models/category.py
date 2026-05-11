"""自定义分类模型 - 支持用户自定义笔记分类"""
import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="分类名称")
    icon: Mapped[str] = mapped_column(String(50), nullable=True, default="📝", comment="分类图标")
    color: Mapped[str] = mapped_column(String(20), nullable=True, default="#6366f1", comment="分类颜色")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序序号")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为内置分类（不可删除）")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        comment="更新时间",
    )

    user = relationship("User", backref="categories")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "icon": self.icon or "📝",
            "color": self.color or "#6366f1",
            "sort_order": self.sort_order,
            "is_builtin": self.is_builtin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
