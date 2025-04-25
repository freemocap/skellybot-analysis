import logging
from pathlib import Path

from skellybot_analysis.db.db_models import Server

logger = logging.getLogger(__name__)
RECORD_OF_PATH_TO_FIND_MOST_RECENT_SCRAPE = Path(__file__).parent / "most_recent_scrape_location.txt"



def get_most_recent_scrape_location() -> str:
    """
    Load txt file that contains the path to the most recent scrape location
    """
    if not Path(RECORD_OF_PATH_TO_FIND_MOST_RECENT_SCRAPE).exists():
        raise FileNotFoundError("No most recent scrape location found")
    try:
        with open((RECORD_OF_PATH_TO_FIND_MOST_RECENT_SCRAPE), "r", encoding='utf-8') as file:
            server_json_path = file.read().strip()

    except OSError:
        raise FileNotFoundError("No most recent scrape location found")

    if not Path(server_json_path).exists():
        raise FileNotFoundError(f"File not found: {server_json_path}")
    return server_json_path

