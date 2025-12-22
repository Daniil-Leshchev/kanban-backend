from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()
def get_db(): db = SessionLocal(); yield db; db.close()


@router.post("/", response_model=schemas.Task)
def create_task(data: schemas.TaskCreate, db: Session = Depends(get_db)):
    obj = models.Task(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/column/{column_id}", response_model=list[schemas.Task])
def list_tasks(column_id: str, db: Session = Depends(get_db)):
    return db.query(models.Task).filter_by(column_id=column_id).order_by(models.Task.order).all()


@router.get("/{task_id}", response_model=schemas.Task)
def get_task(task_id: str, db: Session = Depends(get_db)):
    return db.query(models.Task).get(task_id)


@router.patch("/{task_id}", response_model=schemas.Task)
def update_task(task_id: str, data: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db.query(models.Task).filter_by(id=task_id).update(
        data.dict(exclude_unset=True))
    db.commit()
    return db.query(models.Task).get(task_id)


@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    db.query(models.Task).filter_by(id=task_id).delete()
    db.commit()
    return {"ok": True}
