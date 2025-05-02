import logging

import discord

from skellybot_analysis.old_db.sql_db.sql_db_models.db_server_models import Message
from skellybot_analysis.data_models.server_models import MessageModel

logger = logging.getLogger(__name__)

MINIMUM_THREAD_MESSAGE_COUNT = 4  # Minimum number of messages in a thread to be included in the scraped data
LATEST_MESSAGE_DATETIME = None


def update_latest_message_datetime(message_datetime):
    global LATEST_MESSAGE_DATETIME
    if LATEST_MESSAGE_DATETIME is None or message_datetime > LATEST_MESSAGE_DATETIME:
        LATEST_MESSAGE_DATETIME = message_datetime


async def get_reaction_tagged_messages(channel: discord.TextChannel, target_emoji: str) -> list[str]:
    tagged_messages = []
    async for message in channel.history(limit=None, oldest_first=True):
        if message.reactions:
            for reaction in message.reactions:
                if reaction.emoji == target_emoji:
                    tagged_messages.append(await  MessageModel.from_discord_message(message))
    return [msg.full_content for msg in tagged_messages]


async def get_pinned_message_contents(channel: discord.TextChannel):
    pinned_messages = [await MessageModel.from_discord_message(msg) for msg in await channel.pins()]
    return [msg.full_content for msg in pinned_messages]

async def get_prompts_from_channel(channel: discord.TextChannel, prompt_tag_emoji: str | None = "🤖") -> list[str]:
    prompt_messages = []
    try:
        if hasattr(channel,"topic") and channel.topic:
            prompt_messages.append(channel.topic)
        if prompt_tag_emoji is not None:
            prompt_messages.extend(await get_reaction_tagged_messages(channel=channel, target_emoji=prompt_tag_emoji))
        prompt_messages.extend(await get_pinned_message_contents(channel=channel))
    except discord.Forbidden:
        logger.warning(f"Permission denied to access prompt messages in channel: {channel.name}")
    return prompt_messages
