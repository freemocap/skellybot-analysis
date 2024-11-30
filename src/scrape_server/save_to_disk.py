import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict

from src.models.data_models.server_data.server_data_model import ServerData
from src.scrape_server.save_to_markdown_directory import save_as_markdown_directory
from src.utilities.sanitize_filename import sanitize_name

logger = logging.getLogger(__name__)


def save_server_data_to_json(server_data:ServerData, output_directory: str) -> str:
    directory_path = Path(output_directory)
    if directory_path.is_file():
        full_json_path = directory_path
    else:
        directory_path.mkdir(parents=True, exist_ok=True)
        date_string = datetime.now().isoformat()
        file_name = sanitize_name(f"{server_data.name}_{date_string}")
        full_json_path = str(directory_path / f"{file_name}.json")


    server_data_json = server_data.model_dump_json(indent=2)

    # encoding='utf-8' is necessary to avoid UnicodeEncodeError
    with open(full_json_path, 'w', encoding='utf-8') as f:
        f.write(server_data_json)
    logger.info(f"Saved server data to disk: {full_json_path}")
    return full_json_path

def load_server_data_from_json(json_path: str) -> ServerData:
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            server_data_json = f.read()
        server_data = ServerData(**json.loads(server_data_json))
    except Exception as e:
        raise ValueError(f"Error loading server data from json: {e}")
    return server_data


def save_server_data_to_disk(output_directory: str, server_data: ServerData) ->Dict[str, str]:

    json_save_path = save_server_data_to_json(server_data=server_data, output_directory=output_directory)

    logger.info(f"Saved server data to disk: {json_save_path}")
    try:
        pickle_save_path = json_save_path.replace('.json', '.pkl')
        pickle.dump(server_data, open(pickle_save_path, 'wb'))
        logger.info(f"Saved server data to disk: {pickle_save_path}")
    except Exception as e:
        raise ValueError(f"Error saving server data as pickle: {e}")

    try:
        markdown_save_path = save_as_markdown_directory(server_data=server_data, output_directory=output_directory)
        logger.info(f"Saved server data to disk: {markdown_save_path}")
    except Exception as e:
        raise ValueError(f"Error saving server data as markdown: {e}")

    return {
        "json": json_save_path,
        "pickle": pickle_save_path,
        "markdown": markdown_save_path
    }

