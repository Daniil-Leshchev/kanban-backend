from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app import models, schemas
from app.dependencies.db import get_db

router = APIRouter()


@router.post("/", response_model=schemas.Attachment)
async def create_attachment(
    data: schemas.AttachmentCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = models.Attachment(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/task/{task_id}", response_model=list[schemas.Attachment])
async def list_attachments(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Attachment).where(
            models.Attachment.task_id == task_id
        )
    )
    return result.scalars().all()


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.Attachment).where(
            models.Attachment.id == attachment_id
        )
    )
    await db.commit()

    return {"ok": True}
