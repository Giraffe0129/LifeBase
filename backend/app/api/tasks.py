"""任务 API - CRUD + 拖拽排序 + WebSocket 实时同步（多用户隔离）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.ws_manager import ws_manager
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskUpdate as TaskBulkReorder, TaskResponse

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有任务（按排序序号排列）"""
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user.id)
        .order_by(Task.sort_order, Task.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新任务"""
    # 自动分配 sort_order
    max_order = await db.execute(
        select(Task.sort_order)
        .where(Task.user_id == user.id)
        .order_by(Task.sort_order.desc())
        .limit(1)
    )
    next_order = (max_order.scalar_one_or_none() or 0) + 1

    task = Task(**data.model_dump(), user_id=user.id, sort_order=next_order)
    db.add(task)
    await db.flush()
    await db.refresh(task)
    await ws_manager.broadcast("sync_task", task.to_dict())
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个任务"""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新任务"""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.flush()
    await db.refresh(task)
    await ws_manager.broadcast("sync_task", task.to_dict())
    return task


@router.put("/reorder/bulk", response_model=list[TaskResponse])
async def reorder_tasks(
    data: list[dict],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量更新任务排序"""
    updated_tasks = []
    for item in data:
        task_id = item.get("id")
        sort_order = item.get("sort_order", 0)
        result = await db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user.id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.sort_order = sort_order
            updated_tasks.append(task)

    await db.flush()
    for task in updated_tasks:
        await db.refresh(task)
        await ws_manager.broadcast("sync_task", task.to_dict())
    return updated_tasks


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除任务"""
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await db.delete(task)
    await ws_manager.broadcast("delete_task", {"id": task_id})
