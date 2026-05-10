"""FastAPI 应用入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api import tasks, travel_plans, notes, ws

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    logger.info("正在初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成，服务启动")
    yield
    logger.info("服务关闭")


app = FastAPI(
    title="My Awesome App",
    description="多端互通任务/出行/笔记管理 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(tasks.router)
app.include_router(travel_plans.router)
app.include_router(notes.router)
app.include_router(ws.router)


@app.get("/")
async def root():
    return {"message": "My Awesome App API", "version": "1.0.0", "docs": "/docs"}
