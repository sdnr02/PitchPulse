from typing import Generator
import redis
from sqlalchemy.orm import Session

from core.database import db_manager, redis_manager

def get_db() -> Generator[Session,None,None]:
    """
    FastAPI dependency that provides a SQLAlchemy database session.

    This generator yields a session from the session factory and ensures
    it is always closed, even if an error occurs.
    """
    db_session = None

    try:
        db_session = db_manager.session_factory()
        yield db_session

    finally:
        if db_session:
            db_session.close()

def get_redis() -> redis.Redis:
    """
    FastAPI dependency that provides a Redis client instance.
    """
    return redis_manager.redis_client