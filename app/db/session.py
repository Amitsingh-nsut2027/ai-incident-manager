"""Database engine and session management.

- `engine`        : the low-level connection pool to PostgreSQL.
- `SessionLocal`  : a factory that produces Session objects (one "conversation"
                    with the DB, used for a single unit of work / request).
- `get_db()`      : a FastAPI dependency that hands a Session to an endpoint and
                    guarantees it's closed afterward (even if an error occurs).
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# `pool_pre_ping=True` checks a connection is still alive before using it,
# avoiding "stale connection" errors after the DB or network hiccups.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# autoflush/autocommit=False gives us explicit control over when data is written.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, then always close it.

    This is FastAPI's dependency-injection pattern: an endpoint declares
    `db: Session = Depends(get_db)` and FastAPI runs this generator —
    everything before `yield` is setup, everything after is teardown.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
