from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.dependencies.db import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.Board)
async def create_board(
    data: schemas.BoardCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = models.Board(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/", response_model=list[schemas.Board])
async def list_boards(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Board)
    )
    return result.scalars().all()


@router.get("/{board_id}", response_model=schemas.Board)
async def get_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Board).where(models.Board.id == board_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Board not found")

    return obj


@router.patch("/{board_id}", response_model=schemas.Board)
async def update_board(
    board_id: str,
    data: schemas.BoardBase,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(models.Board)
        .where(models.Board.id == board_id)
        .values(**data.model_dump(exclude_unset=True))
    )
    await db.commit()

    result = await db.execute(
        select(models.Board).where(models.Board.id == board_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Board not found")

    return obj


@router.delete("/{board_id}")
async def delete_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.Board).where(models.Board.id == board_id)
    )
    await db.commit()

    return {"ok": True}
