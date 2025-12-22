from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()
def get_db(): db = SessionLocal(); yield db; db.close()


@router.post("/", response_model=schemas.TaskAssignee)
def add_assignee(data: schemas.TaskAssignee, db: Session = Depends(get_db)):
    obj = models.TaskAssignee(**data.dict())
    db.add(obj)
    db.commit()
    return obj


@router.get("/task/{task_id}", response_model=list[schemas.TaskAssignee])
def list_assignees(task_id: str, db: Session = Depends(get_db)):
    return db.query(models.TaskAssignee).filter_by(task_id=task_id).all()


@router.delete("/{task_id}/{user_id}")
def remove_assignee(task_id: str, user_id: str, db: Session = Depends(get_db)):
    db.query(models.TaskAssignee).filter_by(
        task_id=task_id, user_id=user_id).delete()
    db.commit()
    return {"ok": True}
