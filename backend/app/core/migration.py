"""
数据库迁移辅助 - 处理 v2 → v3 的 schema 变更
SQLAlchemy 的 create_all 不会修改已存在的表，这里用原生 SQL 做增量迁移
"""
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)


async def run_migrations(conn: AsyncConnection):
    """检查并执行所有需要的数据库迁移"""

    # 1. tasks 表 - sort_order + parent_id
    await _add_column_if_not_exists(conn, "tasks", "sort_order", "INTEGER DEFAULT 0")
    await _add_column_if_not_exists(conn, "tasks", "parent_id", "INTEGER REFERENCES tasks(id)")

    # 2. travel_plans 表 - sort_order
    await _add_column_if_not_exists(conn, "travel_plans", "sort_order", "INTEGER DEFAULT 0")

    # 3. notes 表 - sort_order + category_id
    await _add_column_if_not_exists(conn, "notes", "sort_order", "INTEGER DEFAULT 0")
    await _add_column_if_not_exists(conn, "notes", "category_id", "INTEGER REFERENCES categories(id)")

    # 4. 创建 categories 表（如果不存在）
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name VARCHAR(100) NOT NULL,
            icon VARCHAR(50) DEFAULT '📝',
            color VARCHAR(20) DEFAULT '#6366f1',
            sort_order INTEGER DEFAULT 0,
            is_builtin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # 5. 创建 user_settings 表（如果不存在）
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            weather_enabled BOOLEAN DEFAULT 1,
            extras TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # 6. 数据迁移：将旧笔记的 category='life' 映射到该用户的"生活碎片"内置分类
    await _migrate_old_notes_categories(conn)

    logger.info("数据库迁移完成")


async def _add_column_if_not_exists(conn: AsyncConnection, table: str, column: str, definition: str):
    """SQLite 安全地添加列（如果不存在）"""
    try:
        result = await conn.execute(text(f"PRAGMA table_info({table})"))
        columns = [row[1] for row in result.fetchall()]
        if column not in columns:
            logger.info(f"迁移: {table} 表添加 {column} 列")
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
    except Exception as e:
        logger.warning(f"迁移 {table}.{column} 失败: {e}")


async def _migrate_old_notes_categories(conn: AsyncConnection):
    """
    将旧笔记中 category='life' → 关联到 "生活碎片" 内置分类
    将旧笔记中 category='knowledge' → 关联到 "知识点" 内置分类
    """
    try:
        # 获取所有用户的"生活碎片"和"知识点"内置分类ID
        result = await conn.execute(text("""
            SELECT c.id, c.name, c.user_id FROM categories c WHERE c.is_builtin = 1
        """))
        builtin_cats = result.fetchall()

        for cat_id, cat_name, user_id in builtin_cats:
            cat_key = "life" if "生活" in cat_name else "knowledge" if "知识" in cat_name else None
            if not cat_key:
                continue
            # 更新该用户下 category 匹配但没有 category_id 的笔记
            await conn.execute(text(
                "UPDATE notes SET category_id = :cat_id, category = :cat_key "
                "WHERE user_id = :uid AND category = :cat_key AND category_id IS NULL"
            ), {"cat_id": cat_id, "cat_key": cat_key, "uid": user_id})
            logger.info(f"迁移: 用户 {user_id} 的 {cat_name} 笔记已关联 category_id={cat_id}")

    except Exception as e:
        logger.warning(f"笔记分类数据迁移失败: {e}")
