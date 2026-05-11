"""用户认证 请求/响应 数据验证"""
from pydantic import BaseModel, Field
from typing import Optional


class UserRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=100, description="用户名")
    password: str = Field(..., min_length=4, max_length=100, description="密码")


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class QWeatherKeyUpdate(BaseModel):
    qweather_api_key: str = Field("", description="和风天气 API Key")
