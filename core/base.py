from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    
    All model classes should inherit from this base class to be registered
    with SQLAlchemy's metadata registry and enable ORM functionality.
    """
    pass