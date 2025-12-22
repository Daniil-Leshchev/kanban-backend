from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.models import Task as TaskModel
from app.schemas import Task, TaskCreate, TaskUpdate
from app.dependencies.db import get_db


router = APIRouter()


@router.post("/", response_model=Task)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = TaskModel(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/column/{column_id}", response_model=list[Task])
async def list_tasks(
    column_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TaskModel)
        .where(TaskModel.column_id == column_id)
        .order_by(TaskModel.display_order)
    )
    return result.scalars().all()


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TaskModel).where(TaskModel.id == task_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return obj


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(TaskModel)
        .where(TaskModel.id == task_id)
        .values(**data.model_dump(exclude_unset=True))
    )
    await db.commit()

    result = await db.execute(
        select(TaskModel).where(TaskModel.id == task_id)
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
        delete(TaskModel).where(TaskModel.id == task_id)
    )
    await db.commit()

    return {"ok": True}
