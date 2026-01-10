from datetime import datetime, timezone
from app.models import Board, Column as BoardColumn, Task, TaskAssignee, User
from app.dependencies.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import APIRouter, Depends, HTTPException
import uuid
from typing import TypedDict


class WorkloadItem(TypedDict):
    user_id: uuid.UUID
    name: str
    active: int
    completed: int
    overdue: int


router = APIRouter()


@router.get("/{board_id}/stats/summary")
async def board_stats_summary(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    board_exists = await db.scalar(
        select(func.count()).select_from(Board).where(Board.id == board_id)
    )
    if not board_exists:
        raise HTTPException(status_code=404, detail="Board not found")

    columns_result = await db.execute(
        select(BoardColumn.id, BoardColumn.title).where(
            BoardColumn.board_id == board_id)
    )
    columns = columns_result.all()

    if not columns:
        return {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "not_started": 0,
            "overdue": 0,
        }

    column_ids = [c.id for c in columns]
    column_titles = {c.id: c.title for c in columns}

    IN_PROGRESS_TITLES = {"В процессе"}
    DONE_TITLES = {"Готово"}

    tasks_result = await db.execute(
        select(
            Task.id,
            Task.column_id,
            Task.is_completed,
            Task.started_at,
            Task.completed_at,
            Task.deadline,
        ).where(Task.column_id.in_(column_ids))
    )
    tasks = tasks_result.all()

    now = datetime.now(timezone.utc)

    total = len(tasks)
    completed = 0
    in_progress = 0
    not_started = 0
    overdue = 0

    for task in tasks:
        col_title = column_titles.get(task.column_id)

        if task.completed_at is not None or col_title in DONE_TITLES:
            completed += 1
        elif col_title in IN_PROGRESS_TITLES:
            in_progress += 1
        else:
            not_started += 1

        if task.deadline and task.completed_at is None and task.deadline < now:
            overdue += 1

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "overdue": overdue,
    }


@router.get("/{board_id}/stats/priorities")
async def board_stats_priorities(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    board_exists = await db.scalar(
        select(func.count()).select_from(Board).where(Board.id == board_id)
    )
    if not board_exists:
        raise HTTPException(status_code=404, detail="Board not found")

    columns_result = await db.execute(
        select(BoardColumn.id).where(BoardColumn.board_id == board_id)
    )
    column_ids = [row.id for row in columns_result.all()]

    if not column_ids:
        return {
            "priorities": {},
            "completed": {},
            "active": {},
        }

    tasks_result = await db.execute(
        select(
            Task.priority,
            Task.completed_at,
        ).where(Task.column_id.in_(column_ids))
    )
    tasks = tasks_result.all()

    priorities_total: dict[str, int] = {}
    priorities_completed: dict[str, int] = {}
    priorities_active: dict[str, int] = {}

    for task in tasks:
        priority = task.priority or "undefined"

        priorities_total[priority] = priorities_total.get(priority, 0) + 1

        if task.completed_at is not None:
            priorities_completed[priority] = priorities_completed.get(
                priority, 0) + 1
        else:
            priorities_active[priority] = priorities_active.get(
                priority, 0) + 1

    return {
        "priorities": priorities_total,
        "completed": priorities_completed,
        "active": priorities_active,
    }


@router.get("/{board_id}/stats/productivity")
async def board_stats_productivity(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    group: str = "day",  # day | week
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    if group not in {"day", "week"}:
        raise HTTPException(
            status_code=400, detail="group must be 'day' or 'week'")

    board_exists = await db.scalar(
        select(func.count()).select_from(Board).where(Board.id == board_id)
    )
    if not board_exists:
        raise HTTPException(status_code=404, detail="Board not found")

    columns_result = await db.execute(
        select(BoardColumn.id).where(BoardColumn.board_id == board_id)
    )
    column_ids = [row.id for row in columns_result.all()]

    if not column_ids:
        return []

    if group == "day":
        bucket = func.date_trunc("day", Task.completed_at)
    else:
        bucket = func.date_trunc("week", Task.completed_at)

    filters: list = [
        Task.column_id.in_(column_ids),
        Task.completed_at.is_not(None),
    ]

    if date_from is not None:
        filters.append(Task.completed_at >= date_from)

    if date_to is not None:
        filters.append(Task.completed_at <= date_to)

    result = await db.execute(
        select(
            bucket.label("period"),
            func.count(Task.id).label("count"),
        )
        .where(and_(*filters))
        .group_by(bucket)
        .order_by(bucket)
    )

    rows = result.all()

    return [
        {
            "period": row.period,
            "count": row.count,
        }
        for row in rows
    ]


@router.get("/{board_id}/stats/workload")
async def board_stats_workload(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    board_exists = await db.scalar(
        select(func.count()).select_from(Board).where(Board.id == board_id)
    )
    if not board_exists:
        raise HTTPException(status_code=404, detail="Board not found")

    columns_result = await db.execute(
        select(BoardColumn.id).where(BoardColumn.board_id == board_id)
    )
    column_ids = [row.id for row in columns_result.all()]

    if not column_ids:
        return []

    result = await db.execute(
        select(
            Task.id,
            Task.completed_at,
            Task.deadline,
            TaskAssignee.user_id,
            User.name,
        )
        .join(TaskAssignee, TaskAssignee.task_id == Task.id)
        .join(User, User.id == TaskAssignee.user_id)
        .where(Task.column_id.in_(column_ids))
    )
    rows = result.all()

    now = datetime.now(timezone.utc)

    workload: dict[uuid.UUID, WorkloadItem] = {}

    for row in rows:
        user_id = row.user_id
        if user_id not in workload:
            workload[user_id] = {
                "user_id": user_id,
                "name": row.name,
                "active": 0,
                "completed": 0,
                "overdue": 0,
            }

        if row.completed_at is not None:
            if date_from and row.completed_at < date_from:
                continue
            if date_to and row.completed_at > date_to:
                continue
            workload[user_id]["completed"] += 1
            continue

        workload[user_id]["active"] += 1

        if row.completed_at is None and row.deadline and row.deadline < now:
            workload[user_id]["overdue"] += 1

    return list(workload.values())
