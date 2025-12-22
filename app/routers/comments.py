from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()
def get_db(): db = SessionLocal(); yield db; db.close()


@router.post("/", response_model=schemas.Comment)
def create_comment(data: schemas.CommentCreate, db: Session = Depends(get_db)):
    obj = models.Comment(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/task/{task_id}", response_model=list[schemas.Comment])
def list_comments(task_id: str, db: Session = Depends(get_db)):
    return db.query(models.Comment).filter_by(task_id=task_id).all()


@router.delete("/{comment_id}")
def delete_comment(comment_id: str, db: Session = Depends(get_db)):
    db.query(models.Comment).filter_by(id=comment_id).delete()
    db.commit()
    return {"ok": True}
