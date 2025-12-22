from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()
def get_db(): db = SessionLocal(); yield db; db.close()


@router.post("/", response_model=schemas.Subtask)
def create_subtask(data: schemas.SubtaskCreate, db: Session = Depends(get_db)):
    obj = models.Subtask(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/task/{task_id}", response_model=list[schemas.Subtask])
def list_subtasks(task_id: str, db: Session = Depends(get_db)):
    return db.query(models.Subtask).filter_by(task_id=task_id).order_by(models.Subtask.order).all()


@router.patch("/{subtask_id}", response_model=schemas.Subtask)
def update_subtask(subtask_id: str, data: schemas.SubtaskBase, db: Session = Depends(get_db)):
    db.query(models.Subtask).filter_by(
        id=subtask_id).update(data.dict(exclude_unset=True))
    db.commit()
    return db.query(models.Subtask).get(subtask_id)


@router.delete("/{subtask_id}")
def delete_subtask(subtask_id: str, db: Session = Depends(get_db)):
    db.query(models.Subtask).filter_by(id=subtask_id).delete()
    db.commit()
    return {"ok": True}
