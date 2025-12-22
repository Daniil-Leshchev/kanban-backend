from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/kanban"

# engine = create_engine(DATABASE_URL, echo=True, future=True)


# class Base(DeclarativeBase):
#     pass


# SessionLocal = sessionmaker(
#     bind=engine,
#     autocommit=False,
#     autoflush=False,
#     expire_on_commit=False,
# )
