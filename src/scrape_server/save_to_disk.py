import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from src.models.data_models.server_data.server_data_model import ServerData
from src.models.data_models.user_data_model import UserData
from src.utilities.sanitize_filename import sanitize_name

logger = logging.getLogger(__name__)


def save_server_data_to_json(server_data: ServerData, output_json_path: str) -> str:
    if not output_json_path.endswith('.json'):
        raise ValueError(f"Output path must end with .json: {output_json_path}")
    output_json_path = Path(output_json_path)

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    server_data_json = server_data.model_dump_json(indent=2)

    # encoding='utf-8' is necessary to avoid UnicodeEncodeError
    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(server_data_json)
    logger.info(f"Saved server data to disk: {output_json_path}")
    return str(output_json_path)

def save_user_data_to_json(user_data: Dict[int, UserData],
                           output_json_path: str) ->str:
    if not output_json_path.endswith('.json'):
        raise ValueError(f"Output path must end with .json: {output_json_path}")

    output_dict = {user_id: user_data.model_dump_json(indent=2) for user_id, user_data in user_data.items()}

    # encoding='utf-8' is necessary to avoid UnicodeEncodeError
    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(output_dict, indent=2))
    logger.info(f"Saved server data to disk: {output_json_path}")
    return str(output_json_path)