import asyncio
import logging

import discord

from skellybot_analysis.models.data_models.server_data.server_context_route_model import ServerContextRoute
from skellybot_analysis.models.data_models.server_data.server_data_model import ServerData
from skellybot_analysis.models.data_models.server_data.server_data_sub_object_models import DiscordContentMessage, \
    ChatThread, \
    ChannelData, CategoryData

logger = logging.getLogger(__name__)

MINIMUM_THREAD_MESSAGE_COUNT = 4  # Minimum number of messages in a thread to be included in the scraped data

LATEST_MESSAGE_DATETIME = None


def update_latest_message_datetime(message_datetime):
    global LATEST_MESSAGE_DATETIME
    if LATEST_MESSAGE_DATETIME is None or message_datetime > LATEST_MESSAGE_DATETIME:
        LATEST_MESSAGE_DATETIME = message_datetime


def get_checkpoint_name(server_name: str):
    return f"{server_name}_{LATEST_MESSAGE_DATETIME.strftime('%Y-%m-%d_%H-%M-%S')}"


async def get_reaction_tagged_messages(channel: discord.TextChannel, target_emoji: str) -> list[DiscordContentMessage]:
    logger.info(f"Getting bot prompt messages from channel: {channel.name}")
    prompt_messages = []
    async for message in channel.history(limit=None, oldest_first=True):
        if message.reactions:
            for reaction in message.reactions:
                if reaction.emoji == target_emoji:
                    logger.info(
                        f"Found message with target emoji {target_emoji} with content:\n\n{message.clean_content}")
                    prompt_messages.append(await    DiscordContentMessage.from_discord_message(message))

    logger.info(f"Found {len(prompt_messages)} messages with target emoji {target_emoji} in channel: {channel.name}")
    return prompt_messages


async def scrape_chat_thread(thread: discord.Thread) -> ChatThread:
    chat_thread = ChatThread(name=thread.name,
                             id=thread.id,
                             context_route=ServerContextRoute(
                                 server_name=thread.guild.name,
                                 server_id=thread.guild.id,
                                 category_name=(thread.category.name) if thread.category else None,
                                 category_id=(thread.category.id) if thread.category else None,
                                 channel_name=thread.parent.name,
                                 channel_id=thread.parent.id,
                                 thread_name=thread.name,
                                 thread_id=thread.id
                             )
                             )

    async for message in thread.history(limit=None, oldest_first=True):
        if message.content == '' and len(message.attachments) == 0:
            continue
        if message.content.startswith('~'):
            continue
        update_latest_message_datetime(message.created_at)

        chat_thread.messages.append(await DiscordContentMessage.from_discord_message(message))

    # chat_thread.couplets = await build_couplet_list(messages)
    logger.info(f"Found {len(chat_thread.messages)} messages in thread: {thread.name}")
    if len(chat_thread.messages) == 0:
        logger.warning(f"No messages found in thread: {thread.name}")
    return chat_thread


async def scrape_channel(channel: discord.TextChannel) -> ChannelData | None:
    channel_data = ChannelData(name=channel.name,
                               id=channel.id,
                               context_route=ServerContextRoute(
                                   server_name=channel.guild.name,
                                   server_id=channel.guild.id,
                                   category_name=channel.category.name if channel.category else None,
                                   category_id=channel.category.id if channel.category else None,
                                   channel_name=channel.name,
                                   channel_id=channel.id,
                               )
                               )
    channel_data.channel_description_prompt = channel.topic

    try:
        channel_data.messages = [await DiscordContentMessage.from_discord_message(message) async for message in
                                 channel.history(limit=None, oldest_first=True)]
    except discord.Forbidden:
        logger.warning(f"Permission error extracting messages from {channel.name} - skipping!")

    channel_data.pinned_messages = [await DiscordContentMessage.from_discord_message(message) for message in
                                    await channel.pins()]
    threads = channel.threads

    archived_threads = []
    async for thread in channel.archived_threads(limit=None):
        archived_threads.append(thread)
    all_threads = threads + archived_threads
    for thread in all_threads:

        chat_data = await scrape_chat_thread(thread)
        if not chat_data.messages or len(chat_data.messages) < MINIMUM_THREAD_MESSAGE_COUNT:
            continue
        channel_data.chat_threads[f"name:{chat_data.name},id:{chat_data.id}"] = chat_data
        await asyncio.sleep(.1)
    if len(channel_data.chat_threads) == 0:
        logger.warning(f"No chat threads found in channel: {channel.name}")
        return
    else:
        logger.info(f"Processed {len(channel_data.chat_threads.items())} threads in channel: {channel.name}")
    return channel_data


async def scrape_category(category: discord.CategoryChannel) -> CategoryData:
    logger.info(f"\n\n---------------------------\n\n"
                f"Processing category: {category.name}\n\n"
                f"-------------------------\n\n")
    category_data = CategoryData(name=category.name,
                                 id=category.id,
                                 context_route=ServerContextRoute(
                                     server_name=category.guild.name,
                                     server_id=category.guild.id,
                                     category_name=category.name,
                                     category_id=category.id
                                 )
                                 )
    for channel in category.text_channels:
        if 'bot' in channel.name or 'prompt' in channel.name:
            category_data.bot_prompt_messages.extend(await get_reaction_tagged_messages(channel, '🤖'))
        channel_data = await scrape_channel(channel)
        if channel_data is None or (len(channel_data.chat_threads) == 0 and len(channel_data.messages) == 0):
            logger.warning(f"No threads found in channel: {channel.name}")
            continue
        category_data.channels[f"name:{channel.name},id:{channel.id}"] = channel_data

    logger.info(f"Processed {len(category_data.channels.items())} channels in category: {category.name}")
    return category_data


async def scrape_server(target_server: discord.Guild) -> ServerData:
    logger.info(f'Successfully connected to the guild: {target_server.name} (ID: {target_server.id})')

    server_data = ServerData(name=target_server.name,
                             id=target_server.id,
                             context_route=ServerContextRoute(
                                 server_name=target_server.name,
                                 server_id=target_server.id
                             )
                             )
    channels = await target_server.fetch_channels()
    category_channels = [channel for channel in channels if isinstance(channel, discord.CategoryChannel)]

    # Find Top-level bot prompt channels and apply tagged/pinned message to global server prompt
    for channel in channels:
        if not channel.category and ("bot" in channel.name or "prompt" in channel.name):

            logger.info(f"Extracting server-level prompts from channel: {channel.name}")
            server_data.bot_prompt_messages.extend(await get_reaction_tagged_messages(channel, '🤖'))
            server_data.bot_prompt_messages.extend([await DiscordContentMessage.from_discord_message(message)
                                                    for message in await channel.pins()])

    for category in category_channels:
        try:
            category_data = await scrape_category(category)
            if len(category_data.channels) == 0:
                logger.warning(f"No channels found in category: {category.name}")
                continue
            server_data.categories[f"name:{category.name},id:{category.id}"] = category_data

        except discord.Forbidden as e:
            logger.error(f"Skipping category: {category.name} due to missing permissions")
        except Exception as e:
            logger.error(f"Error processing category: {category.name}")
            logger.error(e)
            raise e

    logger.info(f"Processed {len(server_data.categories)} categories in server: {target_server.name}")
    server_data.calculate_graph_data()

    logger.info(f"Finished processing server: {target_server.name} - Stats:\n {server_data.stats}")

    return server_data
