from fastapi import FastAPI

# from .db import Base, engine

# Base.metadata.create_all(bind=engine)

from app.routers import (
    users, boards, columns, tasks, subtasks, comments, attachments, assignees, members
)

app = FastAPI(title="Kanban API")


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(boards.router, prefix="/boards", tags=["boards"])
app.include_router(columns.router, prefix="/columns", tags=["columns"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(subtasks.router, prefix="/subtasks", tags=["subtasks"])
app.include_router(comments.router, prefix="/comments", tags=["comments"])
app.include_router(attachments.router,
                   prefix="/attachments", tags=["attachments"])
app.include_router(assignees.router, prefix="/assignees", tags=["assignees"])
app.include_router(members.router, prefix="/members", tags=["board_members"])


@app.get("/health")
def health():
    return {"status": "ok"}
