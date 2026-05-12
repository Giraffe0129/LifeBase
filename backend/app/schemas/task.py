"""任务请求/响应 数据验证 - 支持排序 + 子任务"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="任务标题")
    description: Optional[str] = Field("", description="任务描述")
    priority: Optional[int] = Field(0, ge=0, le=2, description="优先级: 0=普通 1=重要 2=紧急")
    parent_id: Optional[int] = Field(None, description="父任务ID")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=2)
    sort_order: Optional[int] = None
    parent_id: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    parent_id: Optional[int] = None
    title: str
    description: str
    completed: bool
    priority: int
    sort_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
