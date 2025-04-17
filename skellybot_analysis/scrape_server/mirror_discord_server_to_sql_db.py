import asyncio
import logging

import discord

from skellybot_analysis.scrape_server.discord_server_sql_mapper import DiscordSQLMapper

logger = logging.getLogger(__name__)

# Minimum number of messages in a thread to be included in the scraped data
MINIMUM_THREAD_MESSAGE_COUNT = 4

async def mirror_thread_to_sql(thread: discord.Thread, channel_id: int) -> int:
    """Scrape a thread and save it to the SQL database."""
    logger.info(f"Processing thread: {thread.name}")

    # Save the thread
    db_thread = await DiscordSQLMapper.save_thread(thread, channel_id)

    # Count messages processed
    message_count = 0

    # Process messages
    async for message in thread.history(limit=None, oldest_first=True):
        if message.content == '' and len(message.attachments) == 0:
            continue
        if message.content.startswith('~'):
            continue

        # Save the message
        await DiscordSQLMapper.save_message(
            discord_message=message,
            channel_id=message.channel.id,
            thread_id=thread.id
        )
        message_count += 1

    logger.info(f"Saved {message_count} messages in thread: {thread.name}")
    return message_count

async def mirror_channel_to_sql(channel: discord.TextChannel, category_id: int) -> int:
    """Scrape a channel and its threads and save them to the SQL database."""
    logger.info(f"Processing channel: {channel.name}")

    # Save the channel
    db_channel = await DiscordSQLMapper.save_channel(channel, category_id)

    # Count of all messages processed
    total_message_count = 0

    # Process channel messages
    try:
        async for message in channel.history(limit=None, oldest_first=True):
            if message.content == '' and len(message.attachments) == 0:
                continue
            if message.content.startswith('~'):
                continue

            # Save the message
            await DiscordSQLMapper.save_message(
                discord_message=message,
                channel_id=channel.id
            )
            total_message_count += 1
    except discord.Forbidden:
        logger.warning(f"Permission error extracting messages from {channel.name} - skipping!")

    # Process threads
    thread_count = 0
    for thread in channel.threads:
        message_count = await mirror_thread_to_sql(thread, channel.id)
        if message_count >= MINIMUM_THREAD_MESSAGE_COUNT:
            thread_count += 1
            total_message_count += message_count
        await asyncio.sleep(.1)

    logger.info(f"Processed {thread_count} threads in channel: {channel.name}")
    logger.info(f"Total messages in channel {channel.name}: {total_message_count}")

    return total_message_count

async def mirror_category_to_sql(category: discord.CategoryChannel, server_id: int) -> int:
    """Scrape a category and its channels to the SQL database."""
    logger.info(f"\n\n---------------------------\n\n"
                f"Processing category: {category.name}\n\n"
                f"-------------------------\n\n")

    # Save the category
    db_category = await DiscordSQLMapper.save_category(category, server_id)

    # Count messages processed in this category
    total_message_count = 0
    channel_count = 0

    # Process channels
    for channel in category.text_channels:
        if isinstance(channel, discord.TextChannel):
            message_count = await mirror_channel_to_sql(channel, category.id)
            if message_count > 0:
                channel_count += 1
                total_message_count += message_count

    logger.info(f"Processed {channel_count} channels in category: {category.name}")
    logger.info(f"Total messages in category {category.name}: {total_message_count}")

    return total_message_count

async def mirror_server_to_sql(target_server: discord.Guild) -> int:
    """Scrape an entire server and save it to the SQL database."""
    logger.info(f'Processing server: {target_server.name} (ID: {target_server.id})')

    # Save the server
    db_server = await DiscordSQLMapper.save_server(target_server)

    # Count all messages processed
    total_message_count = 0

    # Get all channels
    channels = await target_server.fetch_channels()

    # Filter for categories
    category_channels = [channel for channel in channels if isinstance(channel, discord.CategoryChannel)]
    category_count = 0

    # Process each category
    for category in category_channels:
        try:
            message_count = await mirror_category_to_sql(category, target_server.id)
            if message_count > 0:
                category_count += 1
                total_message_count += message_count
        except discord.Forbidden as e:
            logger.error(f"Skipping category: {category.name} due to missing permissions")
        except Exception as e:
            logger.error(f"Error processing category: {category.name}")
            logger.error(e)
            raise e

    # Process channels without categories
    for channel in channels:
        if isinstance(channel, discord.TextChannel) and channel.category is None:
            logger.info(f"Processing top-level channel: {channel.name}")
            message_count = await mirror_channel_to_sql(channel, None)
            if message_count > 0:
                total_message_count += message_count

    logger.info(f"Finished processing server: {target_server.name}")
    logger.info(f"Total categories: {category_count}")
    logger.info(f"Total messages: {total_message_count}")

    return total_message_count