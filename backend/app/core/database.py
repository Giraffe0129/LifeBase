"""数据库引擎与会话管理"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.migration import run_migrations

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入 - 获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化/迁移数据库"""
    async with engine.begin() as conn:
        # 1. 创建所有表（仅创建不存在的）
        await conn.run_sync(Base.metadata.create_all)
        # 2. 执行增量迁移（添加列、新建表等）
        await run_migrations(conn)

    logger.info("数据库初始化完成")


def get_sync_session():
    """同步会话 - 用于 Alembic 迁移"""
    from sqlalchemy import create_engine
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncmy", "+mysqldb").replace("+asyncpg", "")
    sync_engine = create_engine(sync_url)
    return sync_engine
