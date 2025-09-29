import os
from typing import Generator, Optional

from loguru import logger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# Retrieving actual database URL from .env or assigning a default url to prevent type error
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db")
REDIS_URL = os.getenv("REDIS_URL")

# Initializing Engine object for managing all connections to a database
engine = create_engine(
    DATABASE_URL,
    # Configuring setting for larger environment
    pool_size=20, # Number of connections to maintain
    max_overflow=30, # Additional connections that can be made when pool is full
    pool_pre_ping=True, # Validates the connections
    pool_recycle=3600, # Recycles the connections every hour
    echo = os.getenv("DEBUG") # Additional logging in debug mode
)

# Initializing session objects for atomic business transactions that are grouped together
local_session = sessionmaker(
    autocommit=False, # Prevents automatic commit of transactions
    autoflush=False, # Prevents automatic temp flush of transactions
    bind=engine # Links the session to the specific database instance
)

# Initializing the base class for database objects like tables to inherit from
base = declarative_base()

class DatabaseManager:
    """
    Class for centralizing all database interactions.
    Contains health checks, connection validation and transaction management.
    """

    def __init__(self):
        self.engine= engine
        self.session = local_session

    def get_session(self) -> Generator[Session,str,str]:
        """
        Generator design pattern to yield a new local session object.

        Generator specific parameters:
        - YieldType (Session): The database session object that is yielded to the caller
        - SendType (str): Command strings that can be sent back to control the session.
            * "commit" - Commits the current transaction
            * "rollback" - Rolls back the current transaction
            * "flush" - Flushes pending changes without committing
        - ReturnType (str): Returns final session status when generator completes:
            * "committed" - Session was successfully committed
            * "rolled_back" - Session was rolled back
            * "error" - An error occurred during session operations
            * "closed" - Session closed normally without explicit commit/rollback

        Usage:
            # Basic usage (no send/return)
            session_gen = db_manager.get_session()
            db = next(session_gen)
            # Use db for queries
            
            # Advanced usage (with send commands)
            session_gen = db_manager.get_session()
            db = next(session_gen)
            db.add(User(name="Alice"))
            session_gen.send("commit")  # Manually commit
        """
        db = local_session()
        final_status = "closed"
        
        try:
            # Initial yield of the session object
            command = yield db

            # Process any commands that are sent to the generator
            if command == "commit":
                db.commit()
                final_status = "committed"
                logger.info("Session committed via send command")

            if command == "rollback":
                db.rollback()
                final_status = "rolled_back"
                logger.info("Session rolled back via send command")

            if command == "flush":
                db.flush()
                final_status = "flushed"
                logger.info("Session flushed via send command")

        except Exception as e:
            final_status = "error"
            logger.error(f"Error while yielding database session: {e}")
            db.rollback()
            raise

        finally:
            db.close()

        return final_status