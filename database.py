from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from settings import settings

DATABASE_URL = settings.database_url

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def ensure_sqlite_schema():
    """
    Lightweight, SQLite-only schema guard.
    Adds new columns (e.g. created_at) without requiring Alembic.
    """
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(logs)")).fetchall()
        if not cols:
            return

        existing = {row[1] for row in cols}  # (cid, name, type, notnull, dflt_value, pk)
        if "created_at" not in existing:
            conn.execute(
                text("ALTER TABLE logs ADD COLUMN created_at DATETIME")
            )
            conn.commit()