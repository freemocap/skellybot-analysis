import logging

import discord
from discord.ext import commands

from skellybot_analysis.ai.db_analyze_server_data import analyze_server_db
from skellybot_analysis.scrape_server.db_save_to_markdown_directory import save_server_db_as_markdown_directory
from skellybot_analysis.scrape_server.run_server_scraper import run_server_scraper
from skellybot_analysis.system.logging_configuration.configure_logging import configure_logging
from skellybot_analysis.utilities.load_env_variables import DISCORD_DEV_BOT_ID, DISCORD_DEV_BOT_TOKEN, OUTPUT_DIRECTORY, \
    TARGET_SERVER_ID

configure_logging()
logger = logging.getLogger(__name__)

# Initialize the Discord client
DISCORD_CLIENT = commands.Bot(command_prefix='!', intents=discord.Intents.all())


@DISCORD_CLIENT.event
async def on_ready():
    logger.info(f'Logged in as {DISCORD_CLIENT.user.name} (ID: {DISCORD_CLIENT.user.id})')
    if not int(DISCORD_DEV_BOT_ID) == DISCORD_CLIENT.user.id:
        raise ValueError("Discord bot ID does not match expected ID")
    await run_server_scraper(discord_client=DISCORD_CLIENT,
                             target_server_id=TARGET_SERVER_ID,
                             output_directory=OUTPUT_DIRECTORY)
    logger.info('------Done!------')
    await DISCORD_CLIENT.close()


DISCORD_CLIENT.run(DISCORD_DEV_BOT_TOKEN)

print("Server Scraper Done!")
if __name__ == "__main__":
    import asyncio
    asyncio.run(analyze_server_db())
    save_server_db_as_markdown_directory()
    print("Server Data Analysis Done!")

