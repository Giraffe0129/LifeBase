"""出行计划 API - CRUD + 天气预报联动"""
import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.ws_manager import ws_manager
from app.models.travel_plan import TravelPlan
from app.schemas.travel_plan import TravelPlanCreate, TravelPlanUpdate, TravelPlanResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/travel-plans", tags=["出行计划"])

# 和风天气 API 端点
QWEATHER_BASE = "https://devapi.qweather.com/v7"


async def fetch_weather(city: str) -> dict | None:
    """
    调用和风天气 API 获取城市天气预报。
    返回天气状况、温度、是否需要带伞等信息。
    """
    if not settings.QWEATHER_API_KEY or settings.QWEATHER_API_KEY == "your_qweather_api_key_here":
        logger.warning("和风天气 API Key 未配置，跳过天气查询")
        return None

    try:
        # 1. 城市搜索获取 Location ID
        async with httpx.AsyncClient(timeout=10) as client:
            geo_resp = await client.get(
                "https://geoapi.qweather.com/v2/city/lookup",
                params={"location": city, "key": settings.QWEATHER_API_KEY},
            )
            if geo_resp.status_code != 200:
                return None
            geo_data = geo_resp.json()
            if geo_data.get("code") != "200" or not geo_data.get("location"):
                return None
            location_id = geo_data["location"][0]["id"]

            # 2. 获取 3 天天气预报
            weather_resp = await client.get(
                f"{QWEATHER_BASE}/weather/3d",
                params={"location": location_id, "key": settings.QWEATHER_API_KEY},
            )
            if weather_resp.status_code != 200:
                return None
            weather_data = weather_resp.json()
            if weather_data.get("code") != "200":
                return None

            today = weather_data["daily"][0]
            weather_code = int(today.get("iconDay", "999"))

            # 判断是否需要带伞（雨雪天气代码）
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
async def list_travel_plans(db: AsyncSession = Depends(get_db)):
    """获取所有出行计划"""
    result = await db.execute(select(TravelPlan).order_by(TravelPlan.plan_date.desc(), TravelPlan.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=TravelPlanResponse, status_code=201)
async def create_travel_plan(data: TravelPlanCreate, db: AsyncSession = Depends(get_db)):
    """创建出行计划（自动查询天气）"""
    plan = TravelPlan(**data.model_dump())

    # 如果有目的地，自动查询天气预报
    if data.destination:
        weather = await fetch_weather(data.destination)
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
async def update_travel_plan(plan_id: int, data: TravelPlanUpdate, db: AsyncSession = Depends(get_db)):
    """更新出行计划"""
    result = await db.execute(select(TravelPlan).where(TravelPlan.id == plan_id))
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


@router.delete("/{plan_id}", status_code=204)
async def delete_travel_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """删除出行计划"""
    result = await db.execute(select(TravelPlan).where(TravelPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="出行计划不存在")

    await db.delete(plan)
    await ws_manager.broadcast("delete_travel_plan", {"id": plan_id})
