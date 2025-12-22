from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()
def get_db(): db = SessionLocal(); yield db; db.close()


@router.post("/", response_model=schemas.Attachment)
def create_attachment(data: schemas.AttachmentCreate, db: Session = Depends(get_db)):
    obj = models.Attachment(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/task/{task_id}", response_model=list[schemas.Attachment])
def list_attachments(task_id: str, db: Session = Depends(get_db)):
    return db.query(models.Attachment).filter_by(task_id=task_id).all()


@router.delete("/{attachment_id}")
def delete_attachment(attachment_id: str, db: Session = Depends(get_db)):
    db.query(models.Attachment).filter_by(id=attachment_id).delete()
    db.commit()
    return {"ok": True}
