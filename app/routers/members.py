from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models import User, BoardMember
from app.dependencies.db import get_db
from app.schemas import MemberCreate, MemberOut

router = APIRouter()


@router.post("/", response_model=MemberOut)
async def add_member(
    data: MemberCreate,
    db: AsyncSession = Depends(get_db),
):
    user = User(name=data.name)
    db.add(user)
    await db.flush()

    member = BoardMember(
        board_id=data.board_id,
        user_id=user.id,
        role=data.role,
    )
    db.add(member)

    await db.commit()
    await db.refresh(member)

    return MemberOut(
        member_id=member.user_id,
        name=user.name,
        role=member.role,
    )


@router.get("/{board_id}", response_model=list[MemberOut])
async def list_members(
    board_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            BoardMember.user_id,
            User.name,
            BoardMember.role,
        )
        .join(User, User.id == BoardMember.user_id)
        .where(BoardMember.board_id == board_id)
    )

    return [
        MemberOut(
            member_id=row.id,
            name=row.name,
            role=row.role,
        )
        for row in result.all()
    ]


@router.delete("/{board_id}/{user_id}")
async def remove_member(
    board_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(BoardMember).where(
            BoardMember.board_id == board_id,
            BoardMember.user_id == user_id,
        )
    )
    await db.commit()

    return {"ok": True}
