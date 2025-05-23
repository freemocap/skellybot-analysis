import logging

import discord
from discord.ext import commands

from skellybot_analysis.scrape_server.run_server_scraper import run_server_scraper
from skellybot_analysis.utilities.load_env_variables import DISCORD_DEV_BOT_ID, DISCORD_DEV_BOT_TOKEN, OUTPUT_DIRECTORY, \
    TARGET_SERVER_ID

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

    # save_db_as_dataframes()
    # save_server_db_as_markdown_directory()
    print("Done!")

