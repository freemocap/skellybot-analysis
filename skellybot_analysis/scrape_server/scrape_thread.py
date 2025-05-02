import logging

import discord

from skellybot_analysis.scrape_server.dataframe_handler import DataframeHandler
from skellybot_analysis.data_models.server_models import UserModel, ThreadModel, MessageModel
from skellybot_analysis.scrape_server.scrape_utils import MINIMUM_THREAD_MESSAGE_COUNT, update_latest_message_datetime
from skellybot_analysis.utilities.extract_attachements_from_discord_message import \
    extract_attachments_from_discord_message
from skellybot_analysis.utilities.load_env_variables import PROF_USER_ID, DISCORD_BOT_ID

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


async def get_thread_messages(thread: discord.Thread) -> list[discord.Message]:
    thread_messages: list[discord.Message] = []
    async for message in thread.history(limit=None, oldest_first=True):
        thread_messages.append(message)

    return thread_messages


async def scrape_thread(df_handler: DataframeHandler,
                        thread: discord.Thread):
    message_count = 0
    thread_messages = await get_thread_messages(thread)

    if thread.name == '.' and all([message.author.bot for message in thread_messages]):
        logger.info(f"Thread {thread.name} (ID: {thread.id}) is empty or only has bot messages.")
        return None

    if all([message.author.id == PROF_USER_ID-1 or message.author.id == DISCORD_BOT_ID for message in thread_messages]):
        logger.info(f"Thread {thread.name} (ID: {thread.id}) is is all bot and/or prof messages.")
        return None



    if thread.name == '.' and len(thread_messages) < MINIMUM_THREAD_MESSAGE_COUNT:
        logger.info(f"Thread `{thread.name}` (ID: {thread.id}) has fewer than {MINIMUM_THREAD_MESSAGE_COUNT} messages.")
        return None

    # Save user info for the thread owner
    df_handler.store(primary_id=thread.owner.id,
                     entity=UserModel(
                         user_id=thread.owner.id,
                         server_id=thread.guild.id,
                         is_bot=thread.owner.bot,
                         joined_at=thread.owner.joined_at
                     ))
    # Save Thread info
    df_handler.store(primary_id=thread.id,
                     entity=ThreadModel(
                         thread_id=thread.id,
                         thread_name=thread.name,
                         server_id=thread.guild.id,
                         server_name=thread.guild.name,
                         category_id=thread.parent.category.id if thread.parent.category else -1,
                         category_name=thread.parent.category.name if thread.parent.category else "none",
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

        # Save message author USER info
        df_handler.store(primary_id=discord_message.author.id,
                         entity=UserModel(
                             user_id=discord_message.author.id,
                             server_id=discord_message.guild.id,
                             is_bot=discord_message.author.bot,
                             joined_at=discord_message.author.joined_at
                         ))

        df_handler.store(primary_id=discord_message.id,
                         entity=await MessageModel.from_discord_message(msg=discord_message,
                                                                        thread=thread))

        message_count += 1
    logger.info(f"✅ Added thread: {thread.name} (ID: {thread.id}) with {message_count} messages.")
    return None





