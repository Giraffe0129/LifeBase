"""任务 API - CRUD + WebSocket 实时同步"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.ws_manager import ws_manager
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """获取所有任务"""
    result = await db.execute(select(Task).order_by(Task.priority.desc(), Task.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    """创建新任务"""
    task = Task(**data.model_dump())
    db.add(task)
    await db.flush()
    await db.refresh(task)
    # WebSocket 广播
    await ws_manager.broadcast("sync_task", task.to_dict())
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    """更新任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
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


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """删除任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await db.delete(task)
    await ws_manager.broadcast("delete_task", {"id": task_id})
