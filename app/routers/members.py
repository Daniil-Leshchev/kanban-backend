from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app import models, schemas
from app.dependencies.db import get_db

router = APIRouter()


@router.post("/", response_model=schemas.BoardMember)
async def add_member(
    data: schemas.BoardMember,
    db: AsyncSession = Depends(get_db),
):
    obj = models.BoardMember(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/{board_id}", response_model=list[schemas.BoardMember])
async def list_members(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.BoardMember).where(
            models.BoardMember.board_id == board_id
        )
    )
    return result.scalars().all()


@router.delete("/{board_id}/{user_id}")
async def remove_member(
    board_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.BoardMember).where(
            models.BoardMember.board_id == board_id,
            models.BoardMember.user_id == user_id,
        )
    )
    await db.commit()

    return {"ok": True}
