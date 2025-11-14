from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from src.database.sqlite_utils import build_sqlite_connect_args, configure_sqlite_engine
from src.database.url_resolver import resolve_sync_database_url

DATABASE_URL = resolve_sync_database_url()

ENGINE_KWARGS: dict[str, object] = {
    "future": True,
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    ENGINE_KWARGS["connect_args"] = build_sqlite_connect_args()
    ENGINE_KWARGS["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **ENGINE_KWARGS)

if DATABASE_URL.startswith("sqlite"):
    configure_sqlite_engine(engine)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_session() -> Generator[Session, None, None]:
    """Provide a SQLAlchemy session scoped to the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
