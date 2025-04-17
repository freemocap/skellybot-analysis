from pathlib import Path

from skellybot_analysis.utilities.get_most_recent_server_data import persist_most_recent_scrape_location
from skellybot_analysis.utilities.sanitize_filename import sanitize_name


import logging
logger = logging.getLogger(__name__)

async def save_stuff(output_directory, server_data, target_server):
    server_output_directory = Path(output_directory) / f"{sanitize_name(target_server.name)}_data"
    latest_message_timestamp = sanitize_name(server_data.latest_message_timestamp.split('.')[0])
    dated_server_str = f"{sanitize_name(target_server.name)}_{latest_message_timestamp}"
    dated_output_directory = server_output_directory / dated_server_str
    dated_output_directory.mkdir(parents=True, exist_ok=True)
    server_stats_json_path = dated_output_directory / f"{dated_server_str}_server_stats.json"
    server_stats_json_path.write_text(server_data.stats.model_dump_json(indent=2), encoding='utf-8')
    server_data_json_path = dated_output_directory / f"{dated_server_str}_server_data.json"
    server_data_json_path.write_text(server_data.model_dump_json(indent=2), encoding='utf-8')
    persist_most_recent_scrape_location(most_recent_server_data_json_path=str(server_data_json_path))
    logger.info(f"Server data saved to: {dated_output_directory}")
