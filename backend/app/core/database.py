import os
import logging
from typing import Generator

import redis
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import  declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/database")
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379")

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

redis_db = redis.Redis.from_url(REDIS_URL)

def get_db() -> Generator[Session,None,None]:
    """Generator function to yield session objects for FastAPI dependency injection"""
    session = SessionLocal()
    try:
        yield session

    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        session.rollback()
        raise

    finally:
        session.close()

def get_redis() -> redis.Redis:
    """Simple function to return the global shared Redis client"""
    return redis_db