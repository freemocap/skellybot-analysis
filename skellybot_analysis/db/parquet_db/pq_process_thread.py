import logging

import discord

from skellybot_analysis.db.parquet_db.parquet_server_models import ParquetDiscordUser, ParquetDiscordThread, \
    ParquetDiscordMessage, extract_attachments
from skellybot_analysis.db.parquet_db.parquet_storage import ParquetStorage
from skellybot_analysis.scrape_server.scrape_utils import MINIMUM_THREAD_MESSAGE_COUNT, update_latest_message_datetime

logger = logging.getLogger(__name__)


async def get_channel_threads(channel: discord.TextChannel) -> list[discord.Thread]:
    try:
        channel_threads = channel.threads
        # get archived (i.e. 'timed out'/'inactive') threads
        async for thread in channel.archived_threads(limit=None):
            channel_threads.append(thread)
    except discord.Forbidden as e:
        logger.warning(f"Cannot access threads for channel {channel.name} (ID: {channel.id})")
        return []
    return channel_threads


async def pq_process_thread(storage: ParquetStorage,
                            thread: discord.Thread):
    message_count = 0
    thread_messages: list[discord.Message] = []
    async for message in thread.history(limit=None, oldest_first=True):
        thread_messages.append(message)

    if thread.name == '.' and all([message.author.bot for message in thread_messages]):
        logger.info(f"Thread {thread.name} (ID: {thread.id}) is empty or only has bot messages.")
        return None

    if thread.name == '.' and len(thread_messages) < MINIMUM_THREAD_MESSAGE_COUNT:
        logger.info(f"Thread `{thread.name}` (ID: {thread.id}) has fewer than {MINIMUM_THREAD_MESSAGE_COUNT} messages.")
        return None

    # Save user info for the thread owner
    storage.save(db_id=thread.owner.id,
                 entity=ParquetDiscordUser(
                     user_id=thread.owner.id,
                     server_id=thread.guild.id,
                     is_bot=thread.owner.bot,
                     joined_at=thread.owner.joined_at
                 ))

    # Save user info for thread
    storage.save(db_id=thread.id,
                 entity=ParquetDiscordThread(
                     thread_id=thread.id,
                     name=thread.name,
                     server_id=thread.guild.id,
                     server_name=thread.guild.name,
                     category_id=thread.parent.category.id if thread.parent.category else None,
                     category_name=thread.parent.category.name if thread.parent.category else None,
                     channel_name=thread.parent.name,
                     channel_id=thread.parent.id,
                     owner_id=thread.owner.id,
                     jump_url=thread.jump_url,
                     created_at=thread.created_at,
                 ))

    for discord_message in thread_messages:
        if not discord_message.content and len(discord_message.attachments) == 0:
            continue
        if discord_message.content.startswith('~'):
            continue
        update_latest_message_datetime(discord_message.created_at)

        # Save message author user info
        storage.save(db_id=discord_message.author.id,
                     entity=ParquetDiscordUser(
                         user_id=discord_message.author.id,
                         server_id=discord_message.guild.id,
                         is_bot=discord_message.author.bot,
                         joined_at=discord_message.author.joined_at
                     ))

        storage.save(db_id=discord_message.id,
                     entity=ParquetDiscordMessage(
                         message_id=discord_message.id,
                         content=discord_message.content,
                         author_id=discord_message.author.id,
                         jump_url=discord_message.jump_url,
                         parent_message_id=discord_message.reference.message_id if discord_message.reference else None,
                         server_id=thread.guild.id,
                         server_name=thread.guild.name,
                         category_id=thread.parent.category.id if thread.parent.category else None,
                         category_name=thread.parent.category.name if thread.parent.category else None,
                         channel_id=thread.parent.id,
                         channel_name=thread.parent.name,
                         thread_id=thread.id,
                         thread_name=thread.name,
                         timestamp=discord_message.created_at,
                         attachments=await extract_attachments(discord_message.attachments),
                         reactions=[reaction.emoji for reaction in discord_message.reactions]
                     ))

        message_count += 1
    logger.info(f"✅ Added thread: {thread.name} (ID: {thread.id}) with {message_count} messages.")
    return None
