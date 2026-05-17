"""SQLAlchemy database session + Base.

Supports both SQLite (local dev) and PostgreSQL (Railway production).
Railway injects DATABASE_URL with `postgres://` scheme — SQLAlchemy 2 requires
`postgresql://`, so we normalize it here.
"""
from sqlalchemy import create_engine, inspect, text
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


# --- Lightweight idempotent migrations -------------------------------------
# `Base.metadata.create_all()` only creates new tables — it never alters existing
# ones. For the small set of evolving columns in this MVP we keep things simple
# and run ADD COLUMN IF NOT EXISTS on startup. For anything more complex we
# would adopt Alembic.

_MIGRATIONS: list[tuple[str, str, str]] = [
    # (table, column, ddl_fragment)
    ("subscriptions", "amount_usd",        "amount_usd FLOAT NOT NULL DEFAULT 0.0"),
    ("subscriptions", "payment_provider",  "payment_provider VARCHAR(32) NOT NULL DEFAULT ''"),
    ("subscriptions", "payment_id",        "payment_id VARCHAR(128) NOT NULL DEFAULT ''"),
    ("subscriptions", "payment_status",    "payment_status VARCHAR(32) NOT NULL DEFAULT ''"),
]


def _apply_migrations() -> None:
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, column, ddl in _MIGRATIONS:
            if table not in existing_tables:
                continue
            cols = {c["name"] for c in insp.get_columns(table)}
            if column in cols:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def init_db() -> None:
    from app.models import user, signal, subscription, news  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _apply_migrations()
