from fastapi import FastAPI, Depends
from app.dependencies.db import get_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware


from app.routers import (
    users, boards, columns, tasks, subtasks, comments, attachments, members
)

app = FastAPI(title="Kanban API")

origins = [
    "http://localhost:5137"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(boards.router, prefix="/boards", tags=["boards"])
app.include_router(columns.router, prefix="/columns", tags=["columns"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(subtasks.router, prefix="/subtasks", tags=["subtasks"])
app.include_router(comments.router, prefix="/comments", tags=["comments"])
app.include_router(attachments.router,
                   prefix="/attachments", tags=["attachments"])
app.include_router(members.router, prefix="/members", tags=["board_members"])


@app.get("/health/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}
