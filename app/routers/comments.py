from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app import models, schemas
from app.dependencies.db import get_db

router = APIRouter()


@router.post("/", response_model=schemas.Comment)
async def create_comment(
    data: schemas.CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = models.Comment(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/task/{task_id}", response_model=list[schemas.Comment])
async def list_comments(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Comment).where(
            models.Comment.task_id == task_id
        )
    )
    return result.scalars().all()


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.Comment).where(
            models.Comment.id == comment_id
        )
    )
    await db.commit()

    return {"ok": True}
