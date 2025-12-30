from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from pydantic import BaseModel
from sqlalchemy import select, delete, update, func
from app.models import Task as TaskModel
from app.models import TaskAssignee as TaskAssigneeModel
from app.schemas import Task, TaskCreate, TaskUpdate
from app.schemas import TaskAssignee
from app.dependencies.db import get_db


router = APIRouter()


class AssigneeAddIn(BaseModel):
    user_id: uuid.UUID


@router.post("/", response_model=Task)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(TaskModel)
        .where(TaskModel.column_id == data.column_id)
        .values(display_order=TaskModel.display_order + 100000)
    )

    await db.execute(
        update(TaskModel)
        .where(TaskModel.column_id == data.column_id)
        .values(display_order=TaskModel.display_order - 99999)
    )

    obj = TaskModel(
        id=uuid.uuid4(),
        title=data.title,
        column_id=data.column_id,
        display_order=0,
    )

    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/column/{column_id}", response_model=list[Task])
async def list_tasks(
    column_id: uuid.UUID,
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
    task_id: uuid.UUID,
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
    task_id: uuid.UUID,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TaskModel).where(TaskModel.id == task_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Task not found")

    payload = data.model_dump(exclude_unset=True)

    if "display_order" in payload and payload["display_order"] < 0:
        raise HTTPException(
            status_code=400,
            detail="display_order must be >= 0"
        )

    await db.execute(
        update(TaskModel)
        .where(TaskModel.id == task_id)
        .values(**payload)
    )
    await db.commit()

    await db.refresh(obj)
    return obj


@router.delete("/{task_id}")
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(TaskModel).where(TaskModel.id == task_id)
    )
    await db.commit()

    return {"ok": True}


@router.post("/{task_id}/assignees", response_model=TaskAssignee)
async def add_assignee_to_task(
    task_id: uuid.UUID,
    data: AssigneeAddIn,
    db: AsyncSession = Depends(get_db),
):
    obj = TaskAssigneeModel(task_id=task_id, user_id=data.user_id)
    db.add(obj)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Cannot assign user to task")

    await db.refresh(obj)
    return obj


@router.get("/{task_id}/assignees", response_model=list[TaskAssignee])
async def list_task_assignees(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TaskAssigneeModel).where(TaskAssigneeModel.task_id == task_id)
    )
    return result.scalars().all()


@router.delete("/{task_id}/assignees/{user_id}")
async def remove_assignee_from_task(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
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
