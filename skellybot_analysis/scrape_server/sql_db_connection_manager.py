from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine
from sqlmodel import SQLModel, Session, create_engine



class DatabaseConnectionManager:
    """
    Manages database connections and sessions using SQLAlchemy/SQLModel.

    This class follows the best practices for managing database connections:
    - Reusing database connections through a cached engine
    - Creating one session per request/operation
    - Managing transactions through context managers
    - Proper error handling with rollbacks
    """

    _engine: Engine = None

    @classmethod
    def initialize(cls, db_path: str) -> Engine:
        """Initialize the database engine with the given connection string."""

        sqlite_url = f"sqlite:///{db_path}"
        cls._engine = create_engine(sqlite_url, echo=True)

        # Create all tables defined in the models
        SQLModel.metadata.create_all(cls._engine)

        return cls._engine

    @classmethod
    def get_engine(cls) -> Engine:
        """Get the SQLAlchemy engine, creating it if necessary."""
        if cls._engine is None:
            raise ValueError("Database engine not initialized")
        return cls._engine

    @classmethod
    @contextmanager
    def get_session(cls) -> Iterator[Session]:
        """
        Create a session context manager that automatically handles
        committing, rolling back, and closing the session.
        """
        session = Session(cls.get_engine())
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @classmethod
    @contextmanager
    def get_session_no_autocommit(cls) -> Iterator[Session]:
        """
        Create a session that doesn't automatically commit - useful when
        explicit transaction control is needed.
        """
        session = Session(cls.get_engine())
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


# For FastAPI dependency injection, create a function that uses the context manager
def get_db_session():
    with DatabaseConnectionManager.get_session() as session:
        yield session