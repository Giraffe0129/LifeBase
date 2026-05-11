"""笔记 API - CRUD + 拖拽排序 + WebSocket 实时同步"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.ws_manager import ws_manager
from app.models.user import User
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(prefix="/api/notes", tags=["值得记录"])


@router.get("/", response_model=list[NoteResponse])
async def list_notes(
    category: str = Query(None, description="按分类筛选: life / knowledge / custom"),
    category_id: int = Query(None, description="按自定义分类ID筛选"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的笔记列表（按排序序号排列）"""
    stmt = select(Note).where(Note.user_id == user.id).order_by(Note.sort_order, Note.created_at.desc())
    if category:
        stmt = stmt.where(Note.category == category)
    if category_id:
        stmt = stmt.where(Note.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(
    data: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建笔记（自动分配序号）"""
    max_order = await db.execute(
        select(Note.sort_order)
        .where(Note.user_id == user.id)
        .order_by(Note.sort_order.desc())
        .limit(1)
    )
    next_order = (max_order.scalar_one_or_none() or 0) + 1

    note = Note(**data.model_dump(), user_id=user.id, sort_order=next_order)
    db.add(note)
    await db.flush()
    await db.refresh(note)
    await ws_manager.broadcast("sync_note", note.to_dict())
    return note


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单条笔记"""
    result = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    data: NoteUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新笔记"""
    result = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    await db.flush()
    await db.refresh(note)
    await ws_manager.broadcast("sync_note", note.to_dict())
    return note


@router.put("/reorder/bulk", response_model=list[NoteResponse])
async def reorder_notes(
    data: list[dict],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量更新笔记排序"""
    updated_notes = []
    for item in data:
        note_id = item.get("id")
        sort_order = item.get("sort_order", 0)
        result = await db.execute(
            select(Note).where(Note.id == note_id, Note.user_id == user.id)
        )
        note = result.scalar_one_or_none()
        if note:
            note.sort_order = sort_order
            updated_notes.append(note)

    await db.flush()
    for note in updated_notes:
        await db.refresh(note)
        await ws_manager.broadcast("sync_note", note.to_dict())
    return updated_notes


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除笔记"""
    result = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    await db.delete(note)
    await ws_manager.broadcast("delete_note", {"id": note_id})
