import logging
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands
from src.configure_logging import configure_logging
from src.models.data_models.server_data.server_data_model import ServerData
from src.scrape_server.save_to_disk import save_server_data_to_json
from src.scrape_server.scrape_server import scrape_server
from src.utilities.get_most_recent_server_data import persist_most_recent_scrape_location
from src.utilities.load_env_variables import DISCORD_DEV_BOT_ID, OUTPUT_DIRECTORY, TARGET_SERVER_ID, \
    DISCORD_DEV_BOT_TOKEN
from src.utilities.sanitize_filename import sanitize_name

configure_logging()
logger = logging.getLogger(__name__)



# Initialize the Discord client
DISCORD_CLIENT = commands.Bot(command_prefix='!', intents=discord.Intents.all())



@DISCORD_CLIENT.event
async def on_ready():
    logger.info(f'Logged in as {DISCORD_CLIENT.user.name} (ID: {DISCORD_CLIENT.user.id})')
    if not int(DISCORD_DEV_BOT_ID) == DISCORD_CLIENT.user.id:
        raise ValueError("Discord bot ID does not match expected ID")
    await main_server_scraper()
    logger.info('------Done!------')
    await DISCORD_CLIENT.close()


async def main_server_scraper():
    target_server = discord.utils.get(DISCORD_CLIENT.guilds, id=int(TARGET_SERVER_ID))
    server_output_directory = Path(OUTPUT_DIRECTORY) / f"{sanitize_name(target_server.name)}_data"
    dated_output_directory = str(server_output_directory / Path(f"{sanitize_name(target_server.name)}_{sanitize_name(datetime.now().isoformat(timespec='minutes'))}"))
    if not target_server:
        logger.error(f"Could not find server with ID: {TARGET_SERVER_ID}")
        raise ValueError(f"Could not find server with ID: {TARGET_SERVER_ID}")

    server_data:ServerData = await scrape_server(target_server)
    json_path = save_server_data_to_json(server_data=server_data,
                                         output_directory=dated_output_directory)

    persist_most_recent_scrape_location(most_recent_server_data_json_path=json_path)



    logger.info(f"Server data saved to: {dated_output_directory}")




DISCORD_CLIENT.run(DISCORD_DEV_BOT_TOKEN)

if __name__ == "__main__":
    import asyncio
    from src.ai.analyze_server_data import process_server_data

    asyncio.run(process_server_data())
    print("Done!")