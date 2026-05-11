"""笔记(值得记录) 请求/响应 数据验证 - 支持自定义分类 + 排序"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="笔记标题")
    content: Optional[str] = Field("", description="笔记内容（支持 Markdown）")
    tags: Optional[str] = Field("", description="标签，逗号分隔")
    category: Optional[str] = Field("life", description="分类标识")
    category_id: Optional[int] = Field(None, description="自定义分类ID")


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    tags: Optional[str] = None
    is_favorite: Optional[bool] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    sort_order: Optional[int] = None


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: str
    is_favorite: bool
    category: str
    category_id: Optional[int] = None
    sort_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
