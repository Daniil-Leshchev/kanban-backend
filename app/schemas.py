import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from app.models import Priority


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
    pass


class Board(BoardBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    owner_id: uuid.UUID

    class Config:
        orm_mode = True


class BoardOut(BoardBase):
    id: uuid.UUID
    owner_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ColumnBase(BaseModel):
    title: str
    display_order: int
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
    title: str
    priority: Optional[Priority] = None
    deadline: Optional[datetime] = None
    display_order: Optional[int] = None


class TaskCreate(TaskBase):
    column_id: uuid.UUID


class TaskUpdate(BaseModel):
    priority: Optional[Priority] = None
    deadline: Optional[datetime] = None
    display_order: Optional[int] = None
    column_id: Optional[uuid.UUID] = None
    is_completed: Optional[bool] = None


class Task(TaskBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    column_id: uuid.UUID
    is_completed: Optional[bool]
    created_by: uuid.UUID | None

    class Config:
        orm_mode = True


class SubtaskBase(BaseModel):
    title: str
    is_completed: bool
    display_order: int


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
    user_id: Optional[uuid.UUID] = None


class Comment(CommentBase):
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
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
    role: str

    class Config:
        orm_mode = True


class MemberCreate(BaseModel):
    board_id: uuid.UUID
    name: str
    role: str


class MemberOut(BaseModel):
    member_id: uuid.UUID
    name: str
    role: str


class BoardViewSubtask(BaseModel):
    id: uuid.UUID
    title: str
    is_completed: bool
    display_order: int


class BoardViewMember(BaseModel):
    member_id: uuid.UUID
    name: str
    role: str


class BoardViewAssignee(BaseModel):
    id: uuid.UUID
    name: str


class BoardViewComment(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    content: str
    user_id: Optional[uuid.UUID]
    created_at: datetime


class BoardViewTask(BaseModel):
    id: uuid.UUID
    title: str
    priority: Optional[Priority] = None
    deadline: Optional[datetime] = None
    display_order: int
    is_completed: bool
    color: Optional[str] = None
    assignees: List[BoardViewAssignee] = []
    subtasks: List[BoardViewSubtask]
    comments: list[BoardViewComment] = []


class BoardViewColumn(BaseModel):
    id: uuid.UUID
    title: str
    display_order: int
    tasks: List[BoardViewTask]


class BoardViewOut(BaseModel):
    id: uuid.UUID
    title: str
    background_color: Optional[str] = None
    members: List[BoardViewMember]
    columns: List[BoardViewColumn]
