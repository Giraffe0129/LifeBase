"""用户设置 API - 功能开关等"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.settings import UserSettings
from app.schemas.settings import UserSettingsUpdate, UserSettingsResponse

router = APIRouter(prefix="/api/settings", tags=["用户设置"])


async def get_or_create_settings(user: User, db: AsyncSession) -> UserSettings:
    """获取或创建用户设置"""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user.id, weather_enabled=True, extras={})
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
    return settings


@router.get("/", response_model=UserSettingsResponse)
async def get_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户设置"""
    settings = await get_or_create_settings(user, db)
    return settings.to_dict()


@router.put("/", response_model=UserSettingsResponse)
async def update_settings(
    data: UserSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户设置"""
    settings = await get_or_create_settings(user, db)

    update_data = data.model_dump(exclude_unset=True)
    if "weather_enabled" in update_data:
        settings.weather_enabled = update_data["weather_enabled"]
    if "extras" in update_data:
        settings.extras = update_data["extras"]

    await db.flush()
    await db.refresh(settings)
    return settings.to_dict()
