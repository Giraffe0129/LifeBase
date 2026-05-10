"""值得记录 / 碎片化知识 数据模型"""
import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="笔记标题")
    content: Mapped[str] = mapped_column(Text, nullable=True, default="", comment="笔记内容（支持 Markdown）")
    tags: Mapped[str] = mapped_column(String(500), nullable=True, default="", comment="标签，逗号分隔")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否收藏")
    category: Mapped[str] = mapped_column(
        String(50), nullable=True, default="life", comment="分类: life(生活碎片) / knowledge(知识点)"
    )
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
            "content": self.content or "",
            "tags": self.tags or "",
            "is_favorite": self.is_favorite,
            "category": self.category or "life",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
