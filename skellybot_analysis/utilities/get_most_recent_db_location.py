import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
RECORD_OF_PATH_TO_FIND_MOST_RECENT_DB = Path(__file__).parent / "most_recent_db_location.txt"


def persist_most_recent_db_location(most_recent_db_path: str) -> None:
    """
    Save the path to the most recent database location to a txt file
    :param most_recent_db_path: Path to the SQLite database file
    :return: None
    """
    if not Path(most_recent_db_path).exists():
        raise FileNotFoundError(f"Database file not found: {most_recent_db_path}")
    with open(RECORD_OF_PATH_TO_FIND_MOST_RECENT_DB, "w", encoding='utf-8') as f:
        f.write(most_recent_db_path)
    logger.info(f"Saved most recent database path: {most_recent_db_path}")


def get_most_recent_db_location() -> str:
    """
    Load txt file that contains the path to the most recent database location
    :return: Path to the most recent database file
    """
    if not Path(RECORD_OF_PATH_TO_FIND_MOST_RECENT_DB).exists():
        raise FileNotFoundError("No most recent database location found")
    try:
        with open((RECORD_OF_PATH_TO_FIND_MOST_RECENT_DB), "r", encoding='utf-8') as file:
            db_path = file.read().strip()

    except OSError:
        raise FileNotFoundError("No most recent database location found")

    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    logger.info(f"Loaded most recent database path: {db_path}")
    return db_path


def get_db_connection_string(db_path: Optional[str] = None) -> str:
    """
    Get a SQLAlchemy connection string for the database
    :param db_path: Optional path to the database. If None, will use the most recent.
    :return: SQLAlchemy connection string
    """
    if db_path is None:
        db_path = get_most_recent_db_location()
    else:
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

    return f"sqlite:///{db_path}"


if __name__ == "__main__":
    # Example usage
    try:
        db_path = get_most_recent_db_location()
        print(f"Most recent database path: {db_path}")
        print(f"Connection string: {get_db_connection_string()}")
    except FileNotFoundError as e:
        print(f"Error: {e}")