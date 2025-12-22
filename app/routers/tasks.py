from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app import models, schemas
from app.dependencies.db import get_db


router = APIRouter()


@router.post("/", response_model=schemas.Task)
async def create_task(
    data: schemas.TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = models.Task(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/column/{column_id}", response_model=list[schemas.Task])
async def list_tasks(
    column_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Task)
        .where(models.Task.column_id == column_id)
        .order_by(models.Task.display_order)
    )
    return result.scalars().all()


@router.get("/{task_id}", response_model=schemas.Task)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return obj


@router.patch("/{task_id}", response_model=schemas.Task)
async def update_task(
    task_id: str,
    data: schemas.TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(models.Task)
        .where(models.Task.id == task_id)
        .values(**data.model_dump(exclude_unset=True))
    )
    await db.commit()

    result = await db.execute(
        select(models.Task).where(models.Task.id == task_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return obj


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.Task).where(models.Task.id == task_id)
    )
    await db.commit()

    return {"ok": True}
