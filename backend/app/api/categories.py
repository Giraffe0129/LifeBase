"""自定义分类 API - CRUD + 内置分类初始化"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.ws_manager import ws_manager
from app.models.user import User
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/api/categories", tags=["自定义分类"])

BUILTIN_CATEGORIES = [
    {"name": "生活碎片", "icon": "🌟", "color": "#f59e0b", "sort_order": 0},
    {"name": "知识点", "icon": "📚", "color": "#6366f1", "sort_order": 1},
]


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有分类（含内置）"""
    # 确保内置分类存在
    for builtin in BUILTIN_CATEGORIES:
        existing = await db.execute(
            select(Category).where(
                Category.user_id == user.id,
                Category.name == builtin["name"],
                Category.is_builtin == True,
            )
        )
        if not existing.scalar_one_or_none():
            cat = Category(
                user_id=user.id,
                name=builtin["name"],
                icon=builtin["icon"],
                color=builtin["color"],
                sort_order=builtin["sort_order"],
                is_builtin=True,
            )
            db.add(cat)
    await db.flush()

    result = await db.execute(
        select(Category)
        .where(Category.user_id == user.id)
        .order_by(Category.sort_order, Category.created_at)
    )
    return result.scalars().all()


@router.post("/", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建自定义分类"""
    # 检查同名分类
    existing = await db.execute(
        select(Category).where(
            Category.user_id == user.id,
            Category.name == data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="同名分类已存在")

    # 获取当前最大 sort_order
    max_order = await db.execute(
        select(Category.sort_order)
        .where(Category.user_id == user.id)
        .order_by(Category.sort_order.desc())
        .limit(1)
    )
    next_order = (max_order.scalar_one_or_none() or 0) + 1

    category = Category(
        user_id=user.id,
        name=data.name,
        icon=data.icon or "📝",
        color=data.color or "#6366f1",
        sort_order=next_order,
        is_builtin=False,
    )
    db.add(category)
    await db.flush()
    await db.refresh(category)

    await ws_manager.broadcast("sync_category", category.to_dict())
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分类"""
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user.id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    await db.flush()
    await db.refresh(category)
    await ws_manager.broadcast("sync_category", category.to_dict())
    return category


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分类（内置分类不可删除）"""
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user.id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    if category.is_builtin:
        raise HTTPException(status_code=400, detail="内置分类不可删除")

    # 将该分类下的笔记设为默认
    from app.models.note import Note
    notes_to_update = await db.execute(
        select(Note).where(Note.category_id == category_id, Note.user_id == user.id)
    )
    for note in notes_to_update.scalars().all():
        note.category_id = None
        note.category = "life"

    await db.delete(category)
    await ws_manager.broadcast("delete_category", {"id": category_id})
