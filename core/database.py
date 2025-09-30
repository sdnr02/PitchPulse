import os
from typing import Generator, Optional

from loguru import logger

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from core.base import Base

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

# Initializing session factory for creating sessions that group atomic business logic
session_factory = sessionmaker(
    autocommit=False, # Prevents automatic commit of transactions
    autoflush=False, # Prevents automatic temp flush of transactions
    bind=engine # Links the session to the specific database instance
)

class DatabaseManager:
    """
    Class for centralizing all database interactions.

    This manager handles database connection pooling, session lifecycle management,
    health checks, connection validation, and transaction management. 
    It provides a centralized interface for all database operations throughout the application.

    Attributes:
        engine: SQLAlchemy engine object for managing all connections to the database.
        session_factory: Factory for creating new database session objects that group atomic business logic.

    Example:
        - db_manager = DatabaseManager()
        - session_gen = db_manager.get_session()
        - db = next(session_gen)
        # Use db for queries
        - db.add(User(name="Alice"))
        - session_gen.send("commit")
    """

    def __init__(self):
        """
        Initalize the DatabaseManager with engine and session factory

        Sets up the database manager with the global engine and session factory
        instances that were configured with connection pooling and transaction management settings.
        """
        self.engine= engine
        self.session_factory = session_factory

    def get_session(self) -> Generator[Session,str,str]:
        """
        Generator design pattern to yield a new local session object.

        This generator method implements the dependency injection pattern to provide
        database sessions with explicit transaction control. 
        It yields a new local session object and accepts commands to control transaction flow 
        (commit, rollback, flush). The generator handles all session lifecycle management
        including error handling and cleanup.

        Yields:
            Session: A new SQLAlchemy database session object for executing queries
                and managing transactions.
        
        Receives:
            str: Optional command strings to control the session:
                - "commit": Commits the current transaction
                - "rollback": Rolls back the current transaction
                - "flush": Flushes pending changes without committing
        
        Returns:
            str: Final session status when generator completes:
                - "committed": Session was successfully committed
                - "rolled_back": Session was rolled back due to explicit command
                - "flushed": Session was flushed without committing
                - "error": An error occurred during session operations
                - "closed": Session closed normally without explicit commit/rollback
        
        Raises:
            Exception: Re-raises any exception that occurs during session operations
                after rolling back the transaction and logging the error.
        
        Example:
            Basic usage (no send/return):
                - session_gen = db_manager.get_session()
                - db = next(session_gen)
                - # Use db for queries
            
            Advanced usage (with send commands):
                - session_gen = db_manager.get_session()
                - db = next(session_gen)
                - db.add(User(name="Alice"))
                - session_gen.send("commit")  # Manually commit
        
        Note:
            The session is automatically closed in the finally block regardless of
            whether the transaction was committed, rolled back, or encountered an error.
            Any uncommitted changes will be rolled back when the session is closed.
        """
        # Calls the factory method to create a new local database session
        db = self.session_factory()
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
            # Exception handling
            final_status = "error"
            logger.error(f"Error while yielding database session: {e}")
            db.rollback()
            raise

        finally:
            # Closing connection post function execution
            db.close()

        return final_status
    
    def health_check(self) -> bool:
        """
        Method to verify if the database is accessible and connection is healthy.

        This method tests the database connection by executing a simple SQL query
        (SELECT 1) against the database. It's typically used for health check endpoints,
        startup validation, or monitoring systems to ensure the database is reachable
        and responding correctly.

        Returns:
            bool: True if the database is accessible and responding correctly,
                  False if the connection fails or returns unexpected results.

        Example:
            - db_manager = DatabaseManager()
            - if db_manager.health_check():
                print("Database is healthy")
              else:
                print("Database is unavailable")

        Note:
            This method creates a temporary connection for the health check and
            automatically closes it after execution. Any exceptions during the
            check are caught, logged, and result in a False return value.
        """
        # Testing connection by running a basic SQL query against the database connection
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                # Fetching the result from the database
                row = result.fetchone()
                if row and row[0] == 1:
                    return True
                else:
                    return False
                
        except Exception as e:
            # Exception Handling
            logger.error(f"Database Health check failed due to error: {e}")
            return False

    def create_all_tables(self) -> None:
        """
        Create all database tables defined by SQLAlchemy models.

        This method creates all tables in the database that are defined by SQLAlchemy
        model classes inheriting from the declarative base. It uses the metadata
        registry to generate CREATE TABLE statements for all registered models.
        This is typically called during application startup or initialization to
        ensure the database schema is properly set up.

        Raises:
            Exception: Re-raises any exception that occurs during table creation
                after logging the error. Common exceptions include connection errors,
                permission issues, or invalid schema definitions.

        Example:
            - db_manager = DatabaseManager()
            - db_manager.create_all_tables()
            # All tables defined in models are now created in the database

        Note:
            This method is idempotent - calling it multiple times will not create
            duplicate tables or raise errors if tables already exist. However, it
            will not modify existing tables or migrate schema changes.
        """
        # Creating the tables defined by SQLAlchemy models
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("All database tables created successfully")

        except Exception as e:
            # Exception Handling
            logger.error(f"Failed to create tables: {e}")
            raise

    def drop_all_tables(self) -> None:
        # Docstring here
        # Deleting all the tables defined by SQLAlchemy models in the metadata
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All database tables dropped")

        except Exception as e:
            # Exception Handling
            logger.error(f"Failed to drop the tables: {e}")
            raise