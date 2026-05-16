"""SQLAlchemy database session + Base.

Supports both SQLite (local dev) and PostgreSQL (Railway production).
Railway injects DATABASE_URL with `postgres://` scheme — SQLAlchemy 2 requires
`postgresql://`, so we normalize it here.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_url = settings.database_url
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}
engine = create_engine(_url, connect_args=connect_args, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import user, signal, subscription, news  # noqa: F401
    Base.metadata.create_all(bind=engine)
