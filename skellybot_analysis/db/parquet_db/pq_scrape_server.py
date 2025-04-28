import logging
from pathlib import Path

import discord

from skellybot_analysis.db.parquet_db.parquet_storage import ParquetStorage
from skellybot_analysis.db.parquet_db.pq_get_context_prompts import grab_context_prompts
from skellybot_analysis.db.parquet_db.pq_process_thread import get_channel_threads, pq_process_thread

logger = logging.getLogger(__name__)


async def pq_scrape_server(target_server: discord.Guild, db_path: str) -> None:
    logger.info(f'Successfully connected to the guild: {target_server.name} (ID: {target_server.id})')
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    all_channels = await target_server.fetch_channels()
    text_channels = [channel for channel in all_channels if isinstance(channel, discord.TextChannel)]
    all_discord_threads: list[discord.Thread] = []
    for channel in text_channels:
        all_discord_threads.extend(await get_channel_threads(channel))

    async with ParquetStorage(str(db_path)) as storage:
        try:
            await grab_context_prompts(storage=storage,
                                       target_server=target_server,
                                       text_channels=text_channels)

            for thread in all_discord_threads:
                await pq_process_thread(storage=storage,
                                        thread=thread)

            logger.info("Server data scraped - Saving to Parquet files...")
        except Exception as e:
            logger.error(f"Critical error during scraping: {str(e)}", exc_info=True)
            raise

    logger.info("✅ All data has been committed to the database")


