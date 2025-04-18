import logging
from pathlib import Path

import discord

from skellybot_analysis.scrape_server.scrape_server import scrape_server
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
    server_name = f"{sanitize_name(target_server.name)}"
    server_output_directory = Path(output_directory) / f"{server_name}_data"
    server_output_directory.mkdir(parents=True, exist_ok=True)
    db_path = server_output_directory  / f"{server_name}.sqlite.db"
    await scrape_server(target_server=target_server, db_path=str(db_path))

