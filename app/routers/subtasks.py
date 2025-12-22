from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app import models, schemas
from app.dependencies.db import get_db

router = APIRouter()


@router.post("/", response_model=schemas.Subtask)
async def create_subtask(
    data: schemas.SubtaskCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = models.Subtask(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/task/{task_id}", response_model=list[schemas.Subtask])
async def list_subtasks(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Subtask)
        .where(models.Subtask.task_id == task_id)
        .order_by(models.Subtask.order)
    )
    return result.scalars().all()


@router.patch("/{subtask_id}", response_model=schemas.Subtask)
async def update_subtask(
    subtask_id: str,
    data: schemas.SubtaskBase,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(models.Subtask)
        .where(models.Subtask.id == subtask_id)
        .values(**data.model_dump(exclude_unset=True))
    )
    await db.commit()

    result = await db.execute(
        select(models.Subtask).where(models.Subtask.id == subtask_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Subtask not found")

    return obj


@router.delete("/{subtask_id}")
async def delete_subtask(
    subtask_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.Subtask).where(models.Subtask.id == subtask_id)
    )
    await db.commit()

    return {"ok": True}
