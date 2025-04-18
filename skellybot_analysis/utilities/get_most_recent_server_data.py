import json
import logging
from pathlib import Path
from pprint import pprint
from typing import Tuple

from skellybot_analysis.models.data_models.server_data.server_data_model import DiscordServer

logger = logging.getLogger(__name__)
RECORD_OF_PATH_TO_FIND_MOST_RECENT_SCRAPE = Path(__file__).parent / "most_recent_scrape_location.txt"


def persist_most_recent_scrape_location(most_recent_server_data_json_path: str) -> None:
    """
    Save the path to the most recent scrape location to a txt file
    :param most_recent_server_data_json_path:
    :return:
    """
    if not Path(most_recent_server_data_json_path).exists():
        raise FileNotFoundError(f"File not found: {most_recent_server_data_json_path}")
    with open(RECORD_OF_PATH_TO_FIND_MOST_RECENT_SCRAPE, "w", encoding='utf-8') as f:
        f.write(most_recent_server_data_json_path)


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


def get_server_data(server_data_json_path: str | None = None) -> Tuple[DiscordServer, str]:
    if server_data_json_path is None:
        json_path = get_most_recent_scrape_location()
    else:
        if not Path(server_data_json_path).exists():
            raise FileNotFoundError(f"File not found: {server_data_json_path}")
        json_path = server_data_json_path
    try:
        logger.info(f"Loading ServerData JSON from: `{json_path}`")
        with open(json_path, "r", encoding='utf-8') as file:
            return DiscordServer(**json.load(file)), json_path
    except OSError:
        raise FileNotFoundError("No most recent server data found")


if __name__ == "__main__":
    pprint(get_most_recent_scrape_location())
    print('\n\n')
    sd = get_server_data()
    pprint(sd.stats())
