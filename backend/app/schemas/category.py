"""自定义分类 请求/响应 数据验证"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    icon: Optional[str] = Field("📝", description="分类图标")
    color: Optional[str] = Field("#6366f1", description="分类颜色")


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    icon: str
    color: str
    sort_order: int
    is_builtin: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
