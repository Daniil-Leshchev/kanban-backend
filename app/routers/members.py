from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()
def get_db(): db = SessionLocal(); yield db; db.close()


@router.post("/", response_model=schemas.BoardMember)
def add_member(data: schemas.BoardMember, db: Session = Depends(get_db)):
    obj = models.BoardMember(**data.dict())
    db.add(obj)
    db.commit()
    return obj


@router.get("/{board_id}", response_model=list[schemas.BoardMember])
def list_members(board_id: str, db: Session = Depends(get_db)):
    return db.query(models.BoardMember).filter_by(board_id=board_id).all()


@router.delete("/{board_id}/{user_id}")
def remove_member(board_id: str, user_id: str, db: Session = Depends(get_db)):
    db.query(models.BoardMember).filter_by(
        board_id=board_id, user_id=user_id).delete()
    db.commit()
    return {"ok": True}
