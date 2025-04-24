from contextlib import contextmanager
from typing import Generator

import pandas as pd
from sqlalchemy import Engine, create_engine
from sqlmodel import SQLModel
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload

from skellybot_analysis.models.db_models.db_ai_analysis_models import ServerObjectAiAnalysis
from skellybot_analysis.models.db_models.db_server_models import User, Thread, Message
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location


def initialize_database_engine(db_path: str|None=None, echo_sql:bool=False) -> Engine:
    if db_path is None:
        db_path = get_most_recent_db_location()
    engine = create_engine(f"sqlite:///{db_path}", echo=echo_sql)
    SQLModel.metadata.create_all(engine)
    return engine

@contextmanager
def get_db_session(db_path: str | None = None) -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Args:
        db_path: Optional path to the database file. If None, uses the most recent database.

    Yields:
        An active database session
    """
    engine:Engine = initialize_database_engine(db_path=db_path)
    session = Session(engine, expire_on_commit=False)  # Set expire_on_commit to False
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_thread_ai_analyses(session: Session | None = None) -> pd.DataFrame:
    """
    Get all thread AI analyses from the database.

    Returns:
        list
    """

