import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger(__name__)

# Handle SQLite vs PostgreSQL configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=False
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session
    and ensures it is properly closed after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session rollback due to error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
