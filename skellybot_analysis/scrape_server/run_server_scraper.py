# skellybot_analysis/scrape_server/run_server_scraper.py
import logging
from pathlib import Path

import discord

from skellybot_analysis.scrape_server.mirror_discord_server_to_sql_db import mirror_server_to_sql
from skellybot_analysis.scrape_server.sql_db_connection_manager import DatabaseConnectionManager
from skellybot_analysis.utilities.sanitize_filename import sanitize_name

logger = logging.getLogger(__name__)

async def run_server_scraper(discord_client: discord.Client,
                            target_server_id: int,
                            output_directory: str):
    """
    Run the server scraper to store Discord data in the SQL database.
    
    Args:
        discord_client: The Discord client for API access
        target_server_id: ID of the server to scrape
        output_directory: Optional directory for any additional files
        
    Returns:
        Total number of messages processed
    """
    # Initialize the database engine if not already initialized

    target_server = discord.utils.get(discord_client.guilds, id=int(target_server_id))

    if not target_server:
        logger.error(f"Could not find server with ID: {target_server_id}")
        raise ValueError(f"Could not find server with ID: {target_server_id}")

    server_db_name = sanitize_name(target_server.name)
    server_db_path = Path(output_directory) / f"{server_db_name}.sqlite.db"
    server_db_path.parent.mkdir(exist_ok=True, parents=True)
    DatabaseConnectionManager.initialize(str(server_db_path))

    # Mirror the server to SQL database
    total_messages = await mirror_server_to_sql(target_server)
    
    logger.info(f"Completed mirroring server {target_server.name} data to sql database at {str(server_db_path)}")
    logger.info(f"Total messages processed: {total_messages}")
    
