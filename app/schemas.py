import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from app.models import Priority
import re


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


class TaskCreate(BaseModel):
    title: str
    column_id: uuid.UUID


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    priority: Optional[Priority] = None
    deadline: Optional[datetime] = None
    display_order: Optional[int] = None
    column_id: Optional[uuid.UUID] = None
    is_completed: Optional[bool] = None
    color: Optional[str] = Field(
        default=None,
    )

    @field_validator("title")
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value.strip():
            raise ValueError("title cannot be empty")
        return value

    @field_validator("color")
    def validate_hex_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not re.fullmatch(r"#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})", value):
            raise ValueError("color must be valid hex color")
        return value


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
    board_id: uuid.UUID
    assignees: List[BoardViewAssignee] = []
    subtasks: List[BoardViewSubtask]
    comments: list[BoardViewComment] = []


class BoardViewColumn(BaseModel):
    id: uuid.UUID
    title: str
    display_order: int
    color: str | None
    tasks: List[BoardViewTask]


class BoardViewOut(BaseModel):
    id: uuid.UUID
    title: str
    background_color: Optional[str] = None
    members: List[BoardViewMember]
    columns: List[BoardViewColumn]


class ColumnReorderPayload(BaseModel):
    column_id: uuid.UUID
    task_ids: List[uuid.UUID]


class BoardReorderPayload(BaseModel):
    columns: List[ColumnReorderPayload]
