from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app import models, schemas
from app.dependencies.db import get_db

router = APIRouter()


@router.post("/", response_model=schemas.User)
async def create_user(
    data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    obj = models.User(**data.model_dump())
    db.add(obj)

    await db.commit()
    await db.refresh(obj)

    return obj


@router.get("/", response_model=list[schemas.User])
async def list_users(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.User)
    )
    return result.scalars().all()


@router.get("/{user_id}", response_model=schemas.User)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status_code=404, detail="User not found")

    return obj


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(models.User).where(models.User.id == user_id)
    )
    await db.commit()

    return {"ok": True}
