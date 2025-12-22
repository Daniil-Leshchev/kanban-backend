from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import uuid
from app.models import Comment as CommentModel
from app.schemas import Comment, CommentCreate
from app.dependencies.db import get_db

router = APIRouter()


@router.post("/", response_model=Comment)
async def create_comment(
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = CommentModel(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/task/{task_id}", response_model=list[Comment])
async def list_comments(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CommentModel).where(
            CommentModel.task_id == task_id
        )
    )
    return result.scalars().all()


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(CommentModel).where(
            CommentModel.id == comment_id
        )
    )
    await db.commit()

    return {"ok": True}
