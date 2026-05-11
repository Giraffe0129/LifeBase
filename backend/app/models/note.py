"""值得记录 / 碎片化知识 数据模型 - 支持自定义分类 + 拖拽排序"""
import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, comment="所属用户")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="笔记标题")
    content: Mapped[str] = mapped_column(Text, nullable=True, default="", comment="笔记内容（支持 Markdown）")
    tags: Mapped[str] = mapped_column(String(500), nullable=True, default="", comment="标签，逗号分隔")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否收藏")
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True, default=None, comment="分类ID"
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=True, default="life", comment="分类标识: life / knowledge / custom"
    )
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

    user = relationship("User", backref="notes")
    category_ref = relationship("Category", backref="notes", foreign_keys=[category_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content or "",
            "tags": self.tags or "",
            "is_favorite": self.is_favorite,
            "category": self.category or "life",
            "category_id": self.category_id,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
