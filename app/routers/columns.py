from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()
def get_db(): db = SessionLocal(); yield db; db.close()


@router.post("/", response_model=schemas.Column)
def create_column(data: schemas.ColumnCreate, db: Session = Depends(get_db)):
    obj = models.Column(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/board/{board_id}", response_model=list[schemas.Column])
def list_board_columns(board_id: str, db: Session = Depends(get_db)):
    return db.query(models.Column).filter_by(board_id=board_id).order_by(models.Column.order).all()


@router.patch("/{column_id}", response_model=schemas.Column)
def update_column(column_id: str, data: schemas.ColumnBase, db: Session = Depends(get_db)):
    db.query(models.Column).filter_by(
        id=column_id).update(data.dict(exclude_unset=True))
    db.commit()
    return db.query(models.Column).get(column_id)


@router.delete("/{column_id}")
def delete_column(column_id: str, db: Session = Depends(get_db)):
    db.query(models.Column).filter_by(id=column_id).delete()
    db.commit()
    return {"ok": True}
