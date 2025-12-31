import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Boolean,
    TIMESTAMP, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy import Enum as SAEnum
from enum import Enum as PyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base


class Priority(PyEnum):
    low = "low"
    medium = "medium"
    high = "high"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String, unique=True)
    avatar_url: Mapped[str | None] = mapped_column(String)

    boards_owned: Mapped[list["Board"]] = relationship(back_populates="owner")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="uploader")
    assignees: Mapped[list["TaskAssignee"]
                      ] = relationship(back_populates="user")
    memberships: Mapped[list["BoardMember"]
                        ] = relationship(back_populates="user")


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    owner: Mapped["User"] = relationship(back_populates="boards_owned")

    columns: Mapped[list["Column"]] = relationship(back_populates="board")
    members: Mapped[list["BoardMember"]] = relationship(back_populates="board")


class Column(Base):
    __tablename__ = "columns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("boards.id"))
    title: Mapped[str] = mapped_column(String)
    display_order: Mapped[int] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    board: Mapped["Board"] = relationship(back_populates="columns")
    tasks: Mapped[list["Task"]] = relationship(back_populates="column")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boards.id"),
        index=True,
        nullable=False,
    )
    column_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("columns.id"))

    title: Mapped[str] = mapped_column(String)
    priority: Mapped[Priority | None] = mapped_column(
        SAEnum(Priority, name="priority_level")
    )
    deadline: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True)
    )
    display_order: Mapped[int] = mapped_column(Integer)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    color: Mapped[str] = mapped_column(String, default='#FFF')

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=True)

    column: Mapped["Column"] = relationship(back_populates="tasks")
    board: Mapped["Board"] = relationship()
    creator: Mapped["User"] = relationship()
    subtasks: Mapped[list["Subtask"]] = relationship(back_populates="task")
    comments: Mapped[list["Comment"]] = relationship(back_populates="task")
    attachments: Mapped[list["Attachment"]
                        ] = relationship(back_populates="task")
    assignees: Mapped[list["TaskAssignee"]
                      ] = relationship(back_populates="task")


class Subtask(Base):
    __tablename__ = "subtasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"))
    title: Mapped[str] = mapped_column(String)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    task: Mapped["Task"] = relationship(back_populates="subtasks")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    task: Mapped["Task"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"))
    file_url: Mapped[str] = mapped_column(String)
    file_name: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    task: Mapped["Task"] = relationship(back_populates="attachments")
    uploader: Mapped["User"] = relationship(back_populates="attachments")


class TaskAssignee(Base):
    __tablename__ = "task_assignees"

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), primary_key=True)

    task: Mapped["Task"] = relationship(back_populates="assignees")
    user: Mapped["User"] = relationship(back_populates="assignees")


class BoardMember(Base):
    __tablename__ = "board_members"

    board_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boards.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String)

    board: Mapped["Board"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")
