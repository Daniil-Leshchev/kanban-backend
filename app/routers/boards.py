from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()
def get_db(): db = SessionLocal(); yield db; db.close()


@router.post("/", response_model=schemas.Board)
def create_board(data: schemas.BoardCreate, db: Session = Depends(get_db)):
    obj = models.Board(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[schemas.Board])
def list_boards(db: Session = Depends(get_db)):
    return db.query(models.Board).all()


@router.get("/{board_id}", response_model=schemas.Board)
def get_board(board_id: str, db: Session = Depends(get_db)):
    return db.query(models.Board).get(board_id)


@router.patch("/{board_id}", response_model=schemas.Board)
def update_board(board_id: str, data: schemas.BoardBase, db: Session = Depends(get_db)):
    db.query(models.Board).filter_by(id=board_id).update(
        data.dict(exclude_unset=True))
    db.commit()
    return db.query(models.Board).get(board_id)


@router.delete("/{board_id}")
def delete_board(board_id: str, db: Session = Depends(get_db)):
    db.query(models.Board).filter_by(id=board_id).delete()
    db.commit()
    return {"ok": True}
