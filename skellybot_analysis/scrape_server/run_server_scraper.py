import logging
from pathlib import Path

import discord

from skellybot_analysis.models.data_models.server_data.server_data_model import ServerData
from skellybot_analysis.scrape_server.scrape_server import scrape_server
from skellybot_analysis.utilities.get_most_recent_server_data import persist_most_recent_scrape_location
from skellybot_analysis.utilities.sanitize_filename import sanitize_name

logger = logging.getLogger(__name__)


async def run_server_scraper(discord_client: discord.Client,
                             target_server_id: int,
                             output_directory: str
                             ):
    target_server = discord.utils.get(discord_client.guilds, id=int(target_server_id))

    if not target_server:
        logger.error(f"Could not find server with ID: {target_server_id}")
        raise ValueError(f"Could not find server with ID: {target_server_id}")

    server_data: ServerData = await scrape_server(target_server)

    server_output_directory = Path(output_directory) / f"{sanitize_name(target_server.name)}_data"

    latest_message_timestamp = sanitize_name(server_data.latest_message_timestamp.split('.')[0])
    dated_server_str = f"{sanitize_name(target_server.name)}_{latest_message_timestamp}"
    dated_output_directory = server_output_directory / dated_server_str
    dated_output_directory.mkdir(parents=True, exist_ok=True)
    server_stats_json_path = dated_output_directory / f"{dated_server_str}_server_stats.json"
    server_stats_json_path.write_text(server_data.stats.model_dump_json(indent=2), encoding='utf-8')
    raw_output_directory = dated_output_directory / "raw_data"
    raw_output_directory.mkdir(parents=True, exist_ok=True)
    server_data_json_path = raw_output_directory / f"{dated_server_str}_server_data.json"
    graph_data_json_path = Path(__file__).parent / 'docs' / 'datasets' / f"{dated_server_str}_graph_data.json"

    server_data_json_path.write_text(server_data.model_dump_json(indent=2), encoding='utf-8')

    # server_graph_data = server_data.calculate_graph_data()
    # graph_data_json_path.write_text(json.dumps(server_graph_data.model_dump(), indent=2), encoding='utf-8')
    persist_most_recent_scrape_location(most_recent_server_data_json_path=str(server_data_json_path))

    logger.info(f"Server data saved to: {dated_output_directory}")
