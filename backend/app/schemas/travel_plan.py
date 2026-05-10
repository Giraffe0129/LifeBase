"""出行计划 请求/响应 数据验证"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TravelPlanCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="出行标题")
    destination: Optional[str] = Field("", description="目的地")
    plan_date: Optional[str] = Field("", description="计划日期 YYYY-MM-DD")
    start_time: Optional[str] = Field("", description="出发时间 HH:MM")
    notes: Optional[str] = Field("", description="备注")


class TravelPlanUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    destination: Optional[str] = None
    plan_date: Optional[str] = None
    start_time: Optional[str] = None
    notes: Optional[str] = None
    completed: Optional[bool] = None


class TravelPlanResponse(BaseModel):
    id: int
    title: str
    destination: str
    plan_date: str
    start_time: str
    notes: str
    need_umbrella: bool
    weather_tip: str
    temperature: str
    completed: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
