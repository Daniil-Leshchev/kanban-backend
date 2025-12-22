from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.dependencies.db import get_db
from app.models import Column as ColumnModel
from app.schemas import Column, ColumnCreate, ColumnBase

router = APIRouter()


@router.post("/", response_model=Column)
async def create_column(
    data: ColumnCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = ColumnModel(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/board/{board_id}", response_model=list[Column])
async def list_board_columns(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ColumnModel)
        .where(ColumnModel.board_id == board_id)
        .order_by(ColumnModel.display_order)
    )
    return result.scalars().all()


@router.patch("/{column_id}", response_model=Column)
async def update_column(
    column_id: str,
    data: ColumnBase,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(ColumnModel)
        .where(ColumnModel.id == column_id)
        .values(**data.model_dump(exclude_unset=True))
    )
    await db.commit()

    result = await db.execute(
        select(ColumnModel).where(ColumnModel.id == column_id)
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
        delete(ColumnModel).where(ColumnModel.id == column_id)
    )
    await db.commit()

    return {"ok": True}
