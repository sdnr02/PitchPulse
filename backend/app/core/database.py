import os
import logging
from typing import Generator

import redis
from dotenv import load_dotenv
import redis.asyncio as aioredis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import  declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/database")

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

REDIS_HOST = "localhost"
REDIS_PORT = 6379
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

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

async_redis_client = None

def get_redis() -> redis.Redis:
    """Method to get the sync Redis client (for publishing)"""
    return redis_client

async def get_async_redis() -> aioredis.Redis:
    """Method to get the async Redis client (for subscribing)"""
    global async_redis_client
    if async_redis_client is None:
        async_redis_client = await aioredis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}",
            decode_responses=True
        )
    return async_redis_client