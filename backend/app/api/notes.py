"""笔记 API - CRUD + WebSocket 实时同步"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.ws_manager import ws_manager
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse

router = APIRouter(prefix="/api/notes", tags=["值得记录"])


@router.get("/", response_model=list[NoteResponse])
async def list_notes(
    category: str = Query(None, description="按分类筛选: life / knowledge"),
    db: AsyncSession = Depends(get_db),
):
    """获取笔记列表，可按分类筛选"""
    stmt = select(Note).order_by(Note.created_at.desc())
    if category:
        stmt = stmt.where(Note.category == category)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(data: NoteCreate, db: AsyncSession = Depends(get_db)):
    """创建笔记"""
    note = Note(**data.model_dump())
    db.add(note)
    await db.flush()
    await db.refresh(note)
    await ws_manager.broadcast("sync_note", note.to_dict())
    return note


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: AsyncSession = Depends(get_db)):
    """获取单条笔记"""
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, data: NoteUpdate, db: AsyncSession = Depends(get_db)):
    """更新笔记"""
    result = await db.execute(select(Note).where(Note.id == note_id))
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


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)):
    """删除笔记"""
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    await db.delete(note)
    await ws_manager.broadcast("delete_note", {"id": note_id})
