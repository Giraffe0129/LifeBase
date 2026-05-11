"""FastAPI 应用入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings as app_settings
from app.core.database import init_db
from app.api import auth, tasks, travel_plans, notes, categories, settings, ws

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成，服务启动")
    yield
    logger.info("服务关闭")


app = FastAPI(
    title="My Awesome App",
    description="多端互通任务/出行/笔记管理 API",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)           # /api/auth/*
app.include_router(tasks.router)          # /api/tasks/*
app.include_router(travel_plans.router)   # /api/travel-plans/*
app.include_router(notes.router)          # /api/notes/*
app.include_router(categories.router)     # /api/categories/*
app.include_router(settings.router)       # /api/settings/*
app.include_router(ws.router)             # /ws


@app.get("/")
async def root():
    return {
        "message": "My Awesome App API v3",
        "version": "3.0.0",
        "docs": "/docs",
        "status": "Cloud-ready with user auth + offline sync + custom categories + drag reorder",
    }
