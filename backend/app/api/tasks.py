"""任务 API - CRUD + 拖拽排序 + 子任务 + WebSocket 实时同步"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.ws_manager import ws_manager
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    parent_id: int = Query(None, description="按父任务ID筛选"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的任务列表。parent_id=None 返回所有，指定则返回子任务"""
    stmt = select(Task).where(Task.user_id == user.id)
    if parent_id is not None:
        stmt = stmt.where(Task.parent_id == parent_id)
    stmt = stmt.order_by(Task.sort_order, Task.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新任务（支持子任务）"""
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
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{task_id}/subtasks", response_model=list[TaskResponse])
async def get_subtasks(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取某个任务的子任务列表"""
    result = await db.execute(
        select(Task).where(Task.parent_id == task_id, Task.user_id == user.id)
        .order_by(Task.sort_order, Task.created_at.desc())
    )
    return result.scalars().all()


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
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
    updated = []
    for item in data:
        task_id = item.get("id")
        sort_order = item.get("sort_order", 0)
        r = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
        t = r.scalar_one_or_none()
        if t: t.sort_order = sort_order; updated.append(t)
    await db.flush()
    for t in updated:
        await db.refresh(t)
        await ws_manager.broadcast("sync_task", t.to_dict())
    return updated


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    # 删除子任务
    await db.execute(select(Task).where(Task.parent_id == task_id))
    await db.delete(task)
    await ws_manager.broadcast("delete_task", {"id": task_id})
