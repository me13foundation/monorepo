import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///med13.db",
)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session
)


def get_session() -> Generator[Session, None, None]:
    """Provide a SQLAlchemy session scoped to the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
