"""
Database engine + session management.

MVP uses SQLite so there is zero setup friction. The connection string is the
ONLY thing that needs to change to move to PostgreSQL later:

    DATABASE_URL = "postgresql://user:password@localhost:5432/finsight"

Everything else (models.py, all queries) is written against the SQLAlchemy
ORM and works unchanged against either backend.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "processed_data", "finsight.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call once on startup."""
    from database import models  # noqa: F401 (ensures models are registered)
    Base.metadata.create_all(bind=engine)
