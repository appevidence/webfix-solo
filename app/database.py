# Ported from appevidence/evidence-capture-app at commit b343b4e8db30a7d620f22e857985ef2cc97fbd57
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db_models import Base


def get_engine(db_path: Path | str | None = None):
    """Create a SQLAlchemy SQLite engine."""
    if db_path is None:
        db_path = settings.resolved_db_path
    db_url = f"sqlite:///{db_path}"
    return create_engine(db_url, connect_args={"check_same_thread": False})


def get_session_factory(engine) -> sessionmaker:
    """Return a session factory bound to the given engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(db_path: Path | str | None = None):
    """Create all tables and return the engine."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def get_session(engine) -> Generator[Session, None, None]:
    """Context manager that yields a SQLAlchemy Session."""
    factory = get_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
