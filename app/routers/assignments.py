from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.dependencies.db import get_db
from app.models import TaskAssignee as TaskAssigneeModel
from app.schemas import TaskAssignee as TaskAssigneeSchema

router = APIRouter()


@router.post("/", response_model=TaskAssigneeSchema)
async def add_assignee(
    data: TaskAssigneeSchema,
    db: AsyncSession = Depends(get_db),
):
    obj = TaskAssigneeModel(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/task/{task_id}", response_model=list[TaskAssigneeSchema])
async def list_assignees(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TaskAssigneeModel).where(
            TaskAssigneeModel.task_id == task_id
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
        delete(TaskAssigneeModel).where(
            TaskAssigneeModel.task_id == task_id,
            TaskAssigneeModel.user_id == user_id,
        )
    )
    await db.commit()

    return {"ok": True}
