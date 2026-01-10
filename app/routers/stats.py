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


class PriorityStats(TypedDict):
    priority: str
    total: int
    completed: int
    active: int


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
        return []

    tasks_result = await db.execute(
        select(
            Task.priority,
            Task.completed_at,
        ).where(Task.column_id.in_(column_ids))
    )
    tasks = tasks_result.all()

    stats: dict[str, PriorityStats] = {}

    for task in tasks:
        priority = task.priority or "undefined"
        if priority not in stats:
            stats[priority] = {
                "priority": priority,
                "total": 0,
                "completed": 0,
                "active": 0,
            }
        stats[priority]["total"] += 1
        if task.completed_at is not None:
            stats[priority]["completed"] += 1
        else:
            stats[priority]["active"] += 1

    return list(stats.values())


@router.get("/{board_id}/stats/productivity")
async def board_stats_productivity(
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
        return {
            "total": 0,
            "completed": 0,
            "active": 0,
            "completed_ratio": 0,
            "active_ratio": 0,
        }

    filters_completed: list = [
        Task.column_id.in_(column_ids),
        Task.completed_at.is_not(None),
    ]
    filters_active: list = [
        Task.column_id.in_(column_ids),
        Task.completed_at.is_(None),
    ]

    if date_from is not None:
        filters_completed.append(Task.completed_at >= date_from)
        filters_active.append(Task.created_at >= date_from)

    if date_to is not None:
        filters_completed.append(Task.completed_at <= date_to)
        filters_active.append(Task.created_at <= date_to)

    completed = await db.scalar(
        select(func.count()).where(and_(*filters_completed))
    ) or 0

    active = await db.scalar(
        select(func.count()).where(and_(*filters_active))
    ) or 0

    total = completed + active

    if total == 0:
        return {
            "total": 0,
            "completed": 0,
            "active": 0,
            "completed_ratio": 0,
            "active_ratio": 0,
        }

    return {
        "total": total,
        "completed": completed,
        "active": active,
        "completed_ratio": completed / total,
        "active_ratio": active / total,
    }


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
            Task.completed_at,
            Task.created_at,
            TaskAssignee.user_id,
            User.name,
        )
        .join(TaskAssignee, TaskAssignee.task_id == Task.id)
        .join(User, User.id == TaskAssignee.user_id)
        .where(Task.column_id.in_(column_ids))
    )

    rows = result.all()

    stats: dict[uuid.UUID, dict] = {}

    for row in rows:
        user_id = row.user_id
        if user_id not in stats:
            stats[user_id] = {
                "user_id": user_id,
                "name": row.name,
                "total": 0,
                "completed": 0,
                "active": 0,
            }

        if row.completed_at:
            if date_from and row.completed_at < date_from:
                continue
            if date_to and row.completed_at > date_to:
                continue
            stats[user_id]["completed"] += 1
            stats[user_id]["total"] += 1
        else:
            if date_from and row.created_at < date_from:
                continue
            if date_to and row.created_at > date_to:
                continue
            stats[user_id]["active"] += 1
            stats[user_id]["total"] += 1

    response = []
    for item in stats.values():
        total = item["total"]
        if total == 0:
            item["completed_ratio"] = 0
            item["active_ratio"] = 0
        else:
            item["completed_ratio"] = item["completed"] / total
            item["active_ratio"] = item["active"] / total
        response.append(item)

    return response
