import os

from loguru import logger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

engine = create_engine(
    DATABASE_URL,
    # Configuring setting for larger environment
    pool_size=20, # Number of connections to maintain
    max_overflow=30, # Additional connections that can be made when pool is full
    pool_pre_ping=True, # Validates the connections
    pool_recycle=3600, # Recycles the connections every hour
    echo = os.getenv("DEBUG") # Additional logging in debug mode
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)