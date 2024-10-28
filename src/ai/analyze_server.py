import json
import pickle
from pathlib import Path

from src.models.server_data_model import ServerData

def load_server_json(server_json_path: Path) -> ServerData:
    with open(server_json_path, 'r', encoding='utf-8') as f:
        server_json = json.load(f)
    return ServerData(**server_json)

def process_server_data(server_data: ServerData) -> ServerData:
    # Do some processing here
    return server_data

if __name__ == "__main__":
    server_json_path = Path(r"C:\Users\jonma\Sync\skellybot-data\HMN_Fall2024_server_data\2024-10-22T06-39\HMN_Fall24_2024-10-22T06-45-19.602861.json")
    server_data = load_server_json(server_json_path)

    processed_server_data = process_server_data(server_data)

    print("Done!")