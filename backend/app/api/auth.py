"""用户认证 API - 注册/登录/配置"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, QWeatherKeyUpdate

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """注册新用户，自动返回 Token"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=user.to_dict())


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=user.to_dict())


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return user.to_dict()


@router.put("/qweather-key")
async def update_qweather_key(
    data: QWeatherKeyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户自己的和风天气 API Key"""
    user.qweather_api_key = data.qweather_api_key
    return {"message": "API Key 已更新", "has_key": bool(data.qweather_api_key)}
