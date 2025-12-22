import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from models import Priority, MemberRole


class UserBase(BaseModel):
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: uuid.UUID

    class Config:
        orm_mode = True


class BoardBase(BaseModel):
    title: str


class BoardCreate(BoardBase):
    owner_id: uuid.UUID


class Board(BoardBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    owner_id: uuid.UUID

    class Config:
        orm_mode = True


class ColumnBase(BaseModel):
    title: str
    order: int
    color: Optional[str] = None


class ColumnCreate(ColumnBase):
    board_id: uuid.UUID


class Column(ColumnBase):
    id: uuid.UUID
    board_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True


class TaskBase(BaseModel):
    description: Optional[str] = None
    priority: Optional[Priority] = None
    deadline: Optional[datetime] = None
    order: int


class TaskCreate(TaskBase):
    column_id: uuid.UUID
    created_by: uuid.UUID


class TaskUpdate(BaseModel):
    description: Optional[str] = None
    priority: Optional[Priority] = None
    deadline: Optional[datetime] = None
    order: Optional[int] = None
    column_id: Optional[uuid.UUID] = None


class Task(TaskBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    column_id: uuid.UUID
    created_by: uuid.UUID

    class Config:
        orm_mode = True


class SubtaskBase(BaseModel):
    title: str
    is_completed: bool
    order: int


class SubtaskCreate(SubtaskBase):
    task_id: uuid.UUID


class Subtask(SubtaskBase):
    id: uuid.UUID
    task_id: uuid.UUID

    class Config:
        orm_mode = True


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    task_id: uuid.UUID
    user_id: uuid.UUID


class Comment(CommentBase):
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True


class AttachmentBase(BaseModel):
    file_url: str
    file_name: str


class AttachmentCreate(AttachmentBase):
    task_id: uuid.UUID
    uploaded_by: uuid.UUID


class Attachment(AttachmentBase):
    id: uuid.UUID
    task_id: uuid.UUID
    uploaded_at: datetime
    uploaded_by: uuid.UUID

    class Config:
        orm_mode = True


class TaskAssignee(BaseModel):
    task_id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        orm_mode = True


class BoardMember(BaseModel):
    board_id: uuid.UUID
    user_id: uuid.UUID
    role: MemberRole

    class Config:
        orm_mode = True
