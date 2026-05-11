"""任务请求/响应 数据验证 - 支持排序"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="任务标题")
    description: Optional[str] = Field("", description="任务描述")
    priority: Optional[int] = Field(0, ge=0, le=2, description="优先级: 0=普通 1=重要 2=紧急")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=2)
    sort_order: Optional[int] = None


class TaskBulkReorder(BaseModel):
    """批量排序请求"""
    orders: List[dict] = Field(..., description="排序列表: [{id: 1, sort_order: 0}, ...]")


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    priority: int
    sort_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
