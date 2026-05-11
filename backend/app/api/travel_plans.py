"""出行计划 API - CRUD + 拖拽排序 + 天气预报联动"""
import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.ws_manager import ws_manager
from app.models.user import User
from app.models.travel_plan import TravelPlan
from app.schemas.travel_plan import TravelPlanCreate, TravelPlanUpdate, TravelPlanResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/travel-plans", tags=["出行计划"])

QWEATHER_BASE = "https://devapi.qweather.com/v7"


async def fetch_weather(city: str, user: User) -> dict | None:
    """调用和风天气 API 获取城市天气预报"""
    api_key = user.qweather_api_key or settings.QWEATHER_API_KEY
    if not api_key:
        logger.warning("用户和全局均未配置和风天气 API Key，跳过天气查询")
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            geo_resp = await client.get(
                "https://geoapi.qweather.com/v2/city/lookup",
                params={"location": city, "key": api_key},
            )
            if geo_resp.status_code != 200:
                return None
            geo_data = geo_resp.json()
            if geo_data.get("code") != "200" or not geo_data.get("location"):
                return None
            location_id = geo_data["location"][0]["id"]

            weather_resp = await client.get(
                f"{QWEATHER_BASE}/weather/3d",
                params={"location": location_id, "key": api_key},
            )
            if weather_resp.status_code != 200:
                return None
            weather_data = weather_resp.json()
            if weather_data.get("code") != "200":
                return None

            today = weather_data["daily"][0]
            weather_code = int(today.get("iconDay", "999"))

            need_umbrella = weather_code in [
                300, 301, 302, 303, 304, 305, 306, 307, 308, 309,
                310, 311, 312, 313, 314, 315, 316, 317, 318, 319,
                320, 321, 399, 400, 401, 402, 403, 404, 405, 406, 407,
            ]

            return {
                "need_umbrella": need_umbrella,
                "weather_tip": f"{today['textDay']}，{today['windDirDay']} {today['windScaleDay']}级",
                "temperature": f"{today['tempMin']}°C ~ {today['tempMax']}°C",
            }

    except Exception as e:
        logger.error(f"天气查询失败: {e}")
        return None


@router.get("/", response_model=list[TravelPlanResponse])
async def list_travel_plans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有出行计划（按排序序号排列）"""
    result = await db.execute(
        select(TravelPlan)
        .where(TravelPlan.user_id == user.id)
        .order_by(TravelPlan.sort_order, TravelPlan.plan_date.desc(), TravelPlan.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=TravelPlanResponse, status_code=201)
async def create_travel_plan(
    data: TravelPlanCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建出行计划（自动查询天气 + 分配序号）"""
    # 自动分配 sort_order
    max_order = await db.execute(
        select(TravelPlan.sort_order)
        .where(TravelPlan.user_id == user.id)
        .order_by(TravelPlan.sort_order.desc())
        .limit(1)
    )
    next_order = (max_order.scalar_one_or_none() or 0) + 1

    plan = TravelPlan(**data.model_dump(), user_id=user.id, sort_order=next_order)

    if data.destination:
        weather = await fetch_weather(data.destination, user)
        if weather:
            plan.need_umbrella = weather["need_umbrella"]
            plan.weather_tip = weather["weather_tip"]
            plan.temperature = weather["temperature"]

    db.add(plan)
    await db.flush()
    await db.refresh(plan)

    await ws_manager.broadcast("sync_travel_plan", plan.to_dict())
    return plan


@router.put("/{plan_id}", response_model=TravelPlanResponse)
async def update_travel_plan(
    plan_id: int,
    data: TravelPlanUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新出行计划"""
    result = await db.execute(select(TravelPlan).where(TravelPlan.id == plan_id, TravelPlan.user_id == user.id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="出行计划不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.flush()
    await db.refresh(plan)
    await ws_manager.broadcast("sync_travel_plan", plan.to_dict())
    return plan


@router.put("/reorder/bulk", response_model=list[TravelPlanResponse])
async def reorder_travel_plans(
    data: list[dict],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量更新出行计划排序"""
    updated_plans = []
    for item in data:
        plan_id = item.get("id")
        sort_order = item.get("sort_order", 0)
        result = await db.execute(
            select(TravelPlan).where(TravelPlan.id == plan_id, TravelPlan.user_id == user.id)
        )
        plan = result.scalar_one_or_none()
        if plan:
            plan.sort_order = sort_order
            updated_plans.append(plan)

    await db.flush()
    for plan in updated_plans:
        await db.refresh(plan)
        await ws_manager.broadcast("sync_travel_plan", plan.to_dict())
    return updated_plans


@router.delete("/{plan_id}", status_code=204)
async def delete_travel_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除出行计划"""
    result = await db.execute(select(TravelPlan).where(TravelPlan.id == plan_id, TravelPlan.user_id == user.id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="出行计划不存在")

    await db.delete(plan)
    await ws_manager.broadcast("delete_travel_plan", {"id": plan_id})
