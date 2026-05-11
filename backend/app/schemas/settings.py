"""用户设置 请求/响应 数据验证"""
from pydantic import BaseModel, Field
from typing import Optional


class UserSettingsUpdate(BaseModel):
    weather_enabled: Optional[bool] = Field(None, description="天气显示开关")
    extras: Optional[dict] = None


class UserSettingsResponse(BaseModel):
    weather_enabled: bool
    extras: dict

    class Config:
        from_attributes = True
