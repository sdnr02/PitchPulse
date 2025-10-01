import os
from contextlib import contextmanager
from typing import Generator, Optional, Dict, List, Any, Sequence

from loguru import logger

from sqlalchemy import create_engine, text, Row
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
        """
        Delete all database tables defined by SQLAlchemy models.

        This method drops (deletes) all tables in the database that are defined by
        SQLAlchemy model classes inheriting from the declarative base. It uses the
        metadata registry to generate DROP TABLE statements for all registered models.
        This is typically used for testing, development resets, or complete database
        cleanup scenarios.

        Raises:
            Exception: Re-raises any exception that occurs during table deletion
                after logging the error. Common exceptions include connection errors,
                permission issues, or foreign key constraint violations.

        Example:
            - db_manager = DatabaseManager()
            - db_manager.drop_all_tables()
            # All tables and their data are now permanently deleted

        Warning:
            This operation is DESTRUCTIVE and IRREVERSIBLE. All data in the tables
            will be permanently lost. Use with extreme caution, preferably only in
            development or testing environments. Never use in production without
            proper backups.

        Note:
            This method may fail if there are foreign key constraints or if other
            database objects depend on these tables. The order of table deletion
            is handled automatically by SQLAlchemy based on foreign key relationships.
        """
        # Deleting all the tables defined by SQLAlchemy models in the metadata
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All database tables dropped")

        except Exception as e:
            # Exception Handling
            logger.error(f"Failed to drop the tables: {e}")
            raise

    def execute_raw_sql(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Sequence[Row[Any]]:
        """
        Execute raw SQL queries directly against the database.

        This method provides a way to execute raw SQL statements when SQLAlchemy's
        ORM capabilities are insufficient or when you need direct SQL control. It
        handles parameter binding to prevent SQL injection and automatically manages
        the database connection lifecycle.

        Args:
            query (str): The raw SQL query string to execute. Use :param_name syntax
                for parameter placeholders (e.g., "SELECT * FROM users WHERE id = :user_id")
            params (Optional[Dict[str, Any]]): Dictionary of parameter names and values
                for parameter binding. Keys should match the placeholders in the query.
                Defaults to None if no parameters are needed.

        Returns:
            Sequence[Row[Any]]: A sequence of Row objects containing the query results.
                Each Row can be accessed like a tuple or dictionary. Returns empty
                sequence if query produces no results.

        Raises:
            Exception: Re-raises any exception that occurs during query execution
                after logging the error. Common exceptions include:
                - Syntax errors in the SQL query
                - Invalid parameter names or types
                - Connection failures
                - Permission/authorization issues

        Example:
            Basic query without parameters:
                - db_manager = DatabaseManager()
                - results = db_manager.execute_raw_sql("SELECT * FROM users")
                - for row in results:
                    print(row.name, row.email)
            
            Query with parameters (prevents SQL injection):
                - query = "SELECT * FROM users WHERE age > :min_age AND city = :city"
                - params = {"min_age": 18, "city": "New York"}
                - results = db_manager.execute_raw_sql(query, params)
            
            Complex query with multiple operations:
                - query = '''
                    WITH active_users AS (
                        SELECT id, name FROM users WHERE status = :status
                    )
                    SELECT * FROM active_users WHERE created_at > :date
                '''
                - params = {"status": "active", "date": "2024-01-01"}
                - results = db_manager.execute_raw_sql(query, params)

        Warning:
            - Use this method sparingly. Prefer SQLAlchemy ORM methods when possible
            for better type safety, query building, and relationship handling.
            - Always use parameter binding (the params argument) instead of string
            formatting to prevent SQL injection attacks.
            - This method creates a new connection for each call. For multiple queries,
            consider using get_session() or get_transaction_session() instead.

        Note:
            - The connection is automatically closed after the query completes
            - This method is read-heavy; for write operations requiring transactions,
            use get_session() or get_transaction_session()
            - Results are not automatically committed; use within a transaction if
            executing INSERT/UPDATE/DELETE statements
        """
        # Connecting to the database for query execution
        try:
            with self.engine.connect() as connection:
                # Running the query against the database
                if params:
                    result = connection.execute(text(query),params)
                else:
                    result = connection.execute(text(query))
                return result.fetchall()
            
        except Exception as e:
            logger.error(f"Raw SQL Execution failed: {e}")
            raise

    @contextmanager
    def get_transaction_session(self) -> Generator[Session,None,None]:
        """
        Context manager to provide a database session with automatic rollback on errors.

        This method implements a context manager pattern for database sessions, making it
        ideal for standalone operations or scripts that need transaction management. Unlike
        get_session(), this is designed to be used with Python's 'with' statement and
        provides automatic rollback on exceptions while requiring explicit commit for
        successful operations.

        Yields:
            Session: A new SQLAlchemy database session object for executing queries
                and managing transactions within the context block.

        Raises:
            Exception: Re-raises any exception that occurs within the context block
                after rolling back the transaction and logging the error.

        Example:
            Basic usage with explicit commit:
                - db_manager = DatabaseManager()
                - with db_manager.get_transaction_session() as session:
                    user = User(name="Alice")
                    session.add(user)
                    session.commit()  # Must explicitly commit
                # Session automatically closed here
            
            Automatic rollback on error:
                - with db_manager.get_transaction_session() as session:
                    user = User(name="Bob")
                    session.add(user)
                    raise ValueError("Something went wrong!")
                    # Rollback happens automatically, Bob is not saved
            
            Complex transaction with multiple operations:
                - with db_manager.get_transaction_session() as session:
                    # Multiple operations in one transaction
                    user = User(name="Charlie")
                    session.add(user)
                    session.flush()  # Get the user.id
                    
                    profile = Profile(user_id=user.id, bio="Developer")
                    session.add(profile)
                    
                    session.commit()  # Commit all changes together
            
            Using with try-except for custom error handling:
                - try:
                    with db_manager.get_transaction_session() as session:
                        user = session.query(User).filter_by(id=1).first()
                        user.name = "Updated Name"
                        session.commit()
                except Exception as e:
                    print(f"Transaction failed: {e}")
                    # Rollback already happened automatically

        Comparison with get_session():
            get_session() (Generator):
                - Designed for FastAPI dependency injection
                - Supports send() commands for fine-grained control
                - Used with Depends() in FastAPI endpoints
                - More flexible but requires understanding generators
            
            get_transaction_session() (Context Manager):
                - Designed for standalone scripts and utility functions
                - Simple 'with' statement usage
                - Explicit commit required
                - Easier to understand and use in non-FastAPI contexts

        Best Practices:
            - Always call session.commit() explicitly to save changes
            - Use for batch operations, data migrations, or standalone scripts
            - Prefer get_session() for FastAPI endpoints
            - Keep transactions short to avoid holding database locks
            - Group related operations in a single transaction for atomicity

        Note:
            - The session is automatically closed in the finally block
            - Any uncommitted changes are lost when the session closes
            - Automatic rollback only happens on exceptions; successful execution
            without commit() will NOT save changes
            - This creates a new session for each 'with' block - don't reuse
        """
        # Initializing the session object using Session factory
        session = self.session_factory()

        # Yielding this session object for the Generator design pattern3
        try:
            yield session

        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed, rolled back: {e}")
            raise

        finally:
            session.close()

# Creating a global database manager instance for Pilot
db_manager = DatabaseManager()