from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app.dependencies.db import get_db
from app.models import Board, User, BoardMember, Column, Task, Subtask, TaskAssignee, Comment
from app.schemas import (
    BoardBase,
    BoardCreate,
    BoardOut,
    BoardViewOut,
    BoardViewColumn,
    BoardViewTask,
    BoardViewSubtask,
    BoardViewMember,
    BoardViewComment,
)


router = APIRouter()

DEFAULT_COLUMNS = [
    {"title": "Бэклог", "display_order": 1},
    {"title": "Сделать", "display_order": 2},
    {"title": "В процессе", "display_order": 3},
    {"title": "Готово", "display_order": 4},
]


@router.post("/", response_model=BoardOut)
async def create_board(
    data: BoardCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = Board(**data.model_dump())
    db.add(obj)

    await db.flush()

    for col in DEFAULT_COLUMNS:
        db.add(
            Column(
                board_id=obj.id,
                title=col["title"],
                display_order=col["display_order"],
            )
        )

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/", response_model=list[BoardOut])
async def list_boards(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Board)
    )
    return result.scalars().all()


@router.get("/{board_id}", response_model=BoardOut)
async def get_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Board not found")

    return obj


@router.patch("/{board_id}", response_model=BoardOut)
async def update_board(
    board_id: str,
    data: BoardBase,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Board)
        .where(Board.id == board_id)
        .values(**data.model_dump(exclude_unset=True))
    )
    await db.commit()

    result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="Board not found")

    return obj


@router.delete("/{board_id}")
async def delete_board(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(Board).where(Board.id == board_id)
    )
    await db.commit()

    return {"ok": True}


@router.get("/{board_id}/view", response_model=BoardViewOut)
async def get_board_view(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    board_result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    board = board_result.scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")

    members_result = await db.execute(
        select(
            BoardMember.user_id,
            User.name,
            BoardMember.role,
        )
        .join(User, User.id == BoardMember.user_id)
        .where(BoardMember.board_id == board_id)
    )
    members = [
        BoardViewMember(
            member_id=row.user_id,
            name=row.name,
            role=row.role,
        )
        for row in members_result.all()
    ]

    columns_result = await db.execute(
        select(Column)
        .where(Column.board_id == board_id)
        .order_by(Column.display_order)
    )
    columns = columns_result.scalars().all()
    column_map = {col.id: col for col in columns}

    tasks_result = await db.execute(
        select(Task)
        .where(Task.column_id.in_(column_map.keys()))
        .order_by(Task.display_order)
    )
    tasks = tasks_result.scalars().all()

    task_ids = [task.id for task in tasks]

    comments_result = await db.execute(
        select(Comment)
        .where(Comment.task_id.in_(task_ids))
        .order_by(Comment.created_at)
    )

    comments = comments_result.scalars().all()

    comments_by_task: dict = {}
    for c in comments:
        comments_by_task.setdefault(c.task_id, []).append(
            BoardViewComment(
                id=c.id,
                task_id=c.task_id,
                content=c.content,
                user_id=c.user_id,
                created_at=c.created_at,
            )
        )

    assignees_result = await db.execute(
        select(
            TaskAssignee.task_id,
            User.id,
            User.name,
        )
        .join(User, User.id == TaskAssignee.user_id)
        .where(TaskAssignee.task_id.in_(task_ids))
    )

    assignees_by_task: dict = {}
    for row in assignees_result.all():
        assignees_by_task.setdefault(row.task_id, []).append(
            {
                "id": row.id,
                "name": row.name,
            }
        )

    subtasks_result = await db.execute(
        select(Subtask)
        .where(Subtask.task_id.in_(task_ids))
        .order_by(Subtask.display_order)
    )
    subtasks = subtasks_result.scalars().all()

    subtasks_by_task: dict = {}
    for sub in subtasks:
        subtasks_by_task.setdefault(sub.task_id, []).append(
            BoardViewSubtask(
                id=sub.id,
                title=sub.title,
                is_completed=sub.is_completed,
                display_order=sub.display_order,
            )
        )

    tasks_by_column: dict = {}
    for task in tasks:
        tasks_by_column.setdefault(task.column_id, []).append(
            BoardViewTask(
                id=task.id,
                title=task.title,
                priority=task.priority,
                deadline=task.deadline,
                is_completed=task.is_completed,
                color=task.color,
                assignees=assignees_by_task.get(task.id, []),
                subtasks=subtasks_by_task.get(task.id, []),
                comments=comments_by_task.get(task.id, []),
            )
        )

    columns_out = []
    for col in columns:
        columns_out.append(
            BoardViewColumn(
                id=col.id,
                title=col.title,
                display_order=col.display_order,
                tasks=tasks_by_column.get(col.id, []),
            )
        )

    return BoardViewOut(
        id=board.id,
        title=board.title,
        background_color=None,
        members=members,
        columns=columns_out,
    )
