from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import uuid
from app.models import Attachment as AttachmentModel
from app.schemas import Attachment, AttachmentCreate
from app.dependencies.db import get_db

router = APIRouter()


@router.post("/", response_model=Attachment)
async def create_attachment(
    data: AttachmentCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = AttachmentModel(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/task/{task_id}", response_model=list[Attachment])
async def list_attachments(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AttachmentModel).where(
            AttachmentModel.task_id == task_id
        )
    )
    return result.scalars().all()


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(AttachmentModel).where(
            AttachmentModel.id == attachment_id
        )
    )
    await db.commit()

    return {"ok": True}
