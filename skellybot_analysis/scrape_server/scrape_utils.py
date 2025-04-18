import logging

import discord

from skellybot_analysis.models.data_models.server_data.server_data_sub_object_models import DiscordContentMessage

logger = logging.getLogger(__name__)

MINIMUM_THREAD_MESSAGE_COUNT = 4  # Minimum number of messages in a thread to be included in the scraped data
LATEST_MESSAGE_DATETIME = None


def update_latest_message_datetime(message_datetime):
    global LATEST_MESSAGE_DATETIME
    if LATEST_MESSAGE_DATETIME is None or message_datetime > LATEST_MESSAGE_DATETIME:
        LATEST_MESSAGE_DATETIME = message_datetime


async def get_reaction_tagged_messages(channel: discord.TextChannel, target_emoji: str) -> list[str]:
    logger.info(f"Getting bot prompt messages from channel: {channel.name}")
    tagged_messages = []
    async for message in channel.history(limit=None, oldest_first=True):
        if message.reactions:
            for reaction in message.reactions:
                if reaction.emoji == target_emoji:
                    logger.info(
                        f"Found message with target emoji {target_emoji} with content:\n\n{message.clean_content}")
                    tagged_messages.append(await  DiscordContentMessage.from_discord_message(message))

    logger.info(f"Found {len(tagged_messages)} messages with target emoji {target_emoji} in channel: {channel.name}")
    return [msg.as_full_text() for msg in tagged_messages]


async def get_pinned_message_contents(channel: discord.TextChannel):
    pinned_messages = [await DiscordContentMessage.from_discord_message(msg) for msg in await channel.pins()]
    return [msg.as_full_text() for msg in pinned_messages]


async def get_prompts_from_channel(channel: discord.TextChannel, prompt_tag_emoji: str | None = None) -> list[str]:
    prompt_messages = []
    if hasattr(channel,"topic") and channel.topic:
        prompt_messages.append(channel.topic)
    if prompt_tag_emoji is not None:
        prompt_messages.extend(await get_reaction_tagged_messages(channel=channel, target_emoji=prompt_tag_emoji))
    prompt_messages.extend(await get_pinned_message_contents(channel=channel))
    return prompt_messages
