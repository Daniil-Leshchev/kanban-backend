from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app import models, schemas

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.User)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    obj = models.User(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[schemas.User])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@router.get("/{user_id}", response_model=schemas.User)
def get_user(user_id: str, db: Session = Depends(get_db)):
    return db.query(models.User).get(user_id)


@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    db.query(models.User).filter_by(id=user_id).delete()
    db.commit()
    return {"ok": True}
