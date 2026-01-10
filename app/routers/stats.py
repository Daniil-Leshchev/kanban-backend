from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.models import Board, Column as BoardColumn, Task, TaskAssignee, User


class PriorityStats(TypedDict):
    priority: str
    total: int
    completed: int
    active: int


class ProductivityStats(TypedDict):
    total: int
    completed: int
    active: int
    completed_ratio: float
    active_ratio: float


class WorkloadStatsItem(TypedDict):
    user_id: uuid.UUID
    name: str
    assigned: int
    workload_ratio: float


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
        select(BoardColumn.id, BoardColumn.title).where(BoardColumn.board_id == board_id)
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
        select(Task.priority, Task.completed_at).where(Task.column_id.in_(column_ids))
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
) -> ProductivityStats:
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
            "completed_ratio": 0.0,
            "active_ratio": 0.0,
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

    completed = (
        await db.scalar(select(func.count()).where(and_(*filters_completed)))
    ) or 0
    active = (await db.scalar(select(func.count()).where(and_(*filters_active)))) or 0
    total = completed + active

    if total == 0:
        return {
            "total": 0,
            "completed": 0,
            "active": 0,
            "completed_ratio": 0.0,
            "active_ratio": 0.0,
        }

    return {
        "total": total,
        "completed": completed,
        "active": active,
        "completed_ratio": completed / total,
        "active_ratio": active / total,
    }


@router.get("/{board_id}/stats/productivity/timeline")
async def board_stats_productivity_timeline(
    board_id: uuid.UUID,
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    step: str = Query("week", regex="^(day|week)$"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
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

    if date_from.tzinfo is None:
        date_from = date_from.replace(tzinfo=timezone.utc)
    else:
        date_from = date_from.astimezone(timezone.utc)
    if date_to.tzinfo is None:
        date_to = date_to.replace(tzinfo=timezone.utc)
    else:
        date_to = date_to.astimezone(timezone.utc)

    from datetime import timedelta

    delta = timedelta(days=1) if step == "day" else timedelta(days=7)

    dates = []
    current_date = date_from
    while current_date <= date_to:
        dates.append(current_date)
        current_date += delta

    response = []

    tasks_query = await db.execute(
        select(
            Task.created_at,
            Task.completed_at,
        ).where(Task.column_id.in_(column_ids))
    )
    tasks = tasks_query.all()

    tasks_data = [(t.created_at, t.completed_at) for t in tasks]

    for d in dates:
        total = 0
        completed = 0
        active = 0

        for created_at, completed_at in tasks_data:
            if created_at is not None and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            elif created_at is not None:
                created_at = created_at.astimezone(timezone.utc)

            if completed_at is not None and completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
            elif completed_at is not None:
                completed_at = completed_at.astimezone(timezone.utc)

            if created_at is not None and created_at <= d:
                total += 1
                if completed_at is not None and completed_at <= d:
                    completed += 1
                elif completed_at is None or completed_at > d:
                    active += 1

        completed_ratio = (completed / total) if total > 0 else 0.0
        active_ratio = (active / total) if total > 0 else 0.0

        response.append({
            "date": d.date().isoformat(),
            "total": total,
            "completed": completed,
            "active": active,
            "completed_ratio": completed_ratio,
            "active_ratio": active_ratio,
        })

    return response


@router.get("/{board_id}/stats/workload")
async def board_stats_workload(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[WorkloadStatsItem]:
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

    query = (
        select(
            User.id.label("user_id"),
            User.name,
            func.count(Task.id).label("assigned_count"),
        )
        .select_from(User)
        .outerjoin(TaskAssignee, TaskAssignee.user_id == User.id)
        .outerjoin(
            Task,
            and_(
                Task.id == TaskAssignee.task_id,
                Task.column_id.in_(column_ids),
                Task.completed_at.is_(None),
            ),
        )
        .group_by(User.id, User.name)
    )

    if date_from is not None:
        query = query.where(
            or_(Task.created_at >= date_from, Task.id.is_(None))
        )

    if date_to is not None:
        query = query.where(
            or_(Task.created_at <= date_to, Task.id.is_(None))
        )

    result = await db.execute(query)
    rows = result.all()

    total_active_assigned = sum(row.assigned_count for row in rows)

    response: list[WorkloadStatsItem] = []
    for row in rows:
        ratio = row.assigned_count / total_active_assigned if total_active_assigned else 0.0
        response.append(
            {
                "user_id": row.user_id,
                "name": row.name,
                "assigned": int(row.assigned_count),
                "workload_ratio": ratio,
            }
        )

    return response


@router.get("/{board_id}/stats/time_by_user")
async def board_stats_time_by_user(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
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

    query = (
        select(
            TaskAssignee.user_id,
            User.name,
            func.sum(func.extract("epoch", Task.completed_at - Task.started_at)).label("seconds"),
        )
        .join(Task, Task.id == TaskAssignee.task_id)
        .join(User, User.id == TaskAssignee.user_id)
        .where(
            Task.column_id.in_(column_ids),
            Task.started_at.is_not(None),
            Task.completed_at.is_not(None),
        )
        .group_by(TaskAssignee.user_id, User.name)
        .order_by(func.sum(func.extract("epoch", Task.completed_at - Task.started_at)).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    response = []
    for row in rows:
        hours = (row.seconds or 0) / 3600
        response.append({
            "user_id": row.user_id,
            "name": row.name,
            "hours": hours,
        })

    return response


@router.get("/{board_id}/stats/completed_tasks_by_user")
async def board_stats_completed_tasks_by_user(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
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

    query = (
        select(
            TaskAssignee.user_id,
            User.name,
            func.count(Task.id).label("completed"),
        )
        .join(Task, Task.id == TaskAssignee.task_id)
        .join(User, User.id == TaskAssignee.user_id)
        .where(
            Task.column_id.in_(column_ids),
            Task.completed_at.is_not(None),
        )
        .group_by(TaskAssignee.user_id, User.name)
        .order_by(func.count(Task.id).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    response = []
    for row in rows:
        response.append({
            "user_id": row.user_id,
            "name": row.name,
            "completed": row.completed,
        })

    return response
