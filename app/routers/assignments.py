from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.dependencies.db import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.TaskAssignee)
async def add_assignee(
    data: schemas.TaskAssignee,
    db: AsyncSession = Depends(get_db),
):
    obj = models.TaskAssignee(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/task/{task_id}", response_model=list[schemas.TaskAssignee])
async def list_assignees(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.TaskAssignee).where(
            models.TaskAssignee.task_id == task_id
        )
    )
    return result.scalars().all()


@router.delete("/{task_id}/{user_id}")
async def remove_assignee(
    task_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.TaskAssignee).where(
            models.TaskAssignee.task_id == task_id,
            models.TaskAssignee.user_id == user_id,
        )
    )
    await db.commit()

    return {"ok": True}
