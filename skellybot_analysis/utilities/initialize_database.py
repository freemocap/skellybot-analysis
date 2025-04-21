from sqlalchemy import Engine, create_engine
from sqlmodel import SQLModel

from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location


def initialize_database_engine(db_path: str|None=None, echo_sql:bool=False) -> Engine:
    if db_path is None:
        db_path = get_most_recent_db_location()
    engine = create_engine(f"sqlite:///{db_path}", echo=echo_sql)
    SQLModel.metadata.create_all(engine)
    return engine
