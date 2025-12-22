from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.dependencies.db import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.Column)
async def create_column(
    data: schemas.ColumnCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = models.Column(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/board/{board_id}", response_model=list[schemas.Column])
async def list_board_columns(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Column)
        .where(models.Column.board_id == board_id)
        .order_by(models.Column.order)
    )
    return result.scalars().all()


@router.patch("/{column_id}", response_model=schemas.Column)
async def update_column(
    column_id: str,
    data: schemas.ColumnBase,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(models.Column)
        .where(models.Column.id == column_id)
        .values(**data.model_dump(exclude_unset=True))
    )
    await db.commit()

    result = await db.execute(
        select(models.Column).where(models.Column.id == column_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Column not found")

    return obj


@router.delete("/{column_id}")
async def delete_column(
    column_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.Column).where(models.Column.id == column_id)
    )
    await db.commit()

    return {"ok": True}
