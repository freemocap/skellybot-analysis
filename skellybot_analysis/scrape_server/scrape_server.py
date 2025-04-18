import logging
from copy import copy

import logging
from copy import copy

import aiohttp
import discord
from sqlmodel import Session, create_engine, SQLModel

from skellybot_analysis.models.data_models.server_data.server_data_model import DiscordServer, ContextSystemPrompt, \
    DiscordCategory, DiscordThread, DiscordMessage
from skellybot_analysis.models.data_models.server_data.server_data_sub_object_models import DiscordContentMessage, \
    ChannelData

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


async def extract_attachment_text(attachment: discord.Attachment) -> str:
    """
    Extract the text from a discord attachment.
    """
    attachment_string = f"START [{attachment.filename}]({attachment.url})"
    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as resp:
            if resp.status == 200:
                try:
                    attachment_string += await resp.text()
                except UnicodeDecodeError:
                    attachment_string += await resp.text(errors='replace')
    attachment_string += f" END [{attachment.filename}]({attachment.url})"
    return attachment_string


async def scrape_server(target_server: discord.Guild, db_path: str):
    logger.info(f'Successfully connected to the guild: {target_server.name} (ID: {target_server.id})')
    engine = create_engine(f"sqlite:///{db_path}", echo=True)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        server_prompt_messages = []
        discord_server = DiscordServer(name=target_server.name,
                               id=target_server.id,
                               categories=[])

        channels = await target_server.fetch_channels()

        for channel in channels:
            if not channel.category and ("bot" in channel.name or "prompt" in channel.name):
                logger.info(f"Extracting server-level prompts from channel: {channel.name}")
                server_prompt_messages.extend(await get_reaction_tagged_messages(channel, '🤖'))
                server_prompt_messages.extend(
                    await DiscordContentMessage.from_discord_message(message) for message in await channel.pins())
                session.add(ContextSystemPrompt(
                    server_id=target_server.id,
                    system_prompt="\n".join(server_prompt_messages)
                ))

        for category in [channel for channel in channels if isinstance(channel, discord.CategoryChannel)]:
            discord_server.categories.append(category.id)
            category_prompts = copy(server_prompt_messages)
            logger.info(f"\n\n---------------------------\n\n"
                        f"Processing category: {category.name}\n\n"
                        f"-------------------------\n\n")
            discord_category = DiscordCategory(name=category.name,
                                       id=category.id,
                                       server_name=category.guild.name,
                                       server_id=category.guild.id,
                                       channels=[]
                                       )
            for channel in category.text_channels:
                if 'bot' in channel.name or 'prompt' in channel.name:
                    category_prompts.extend(await get_reaction_tagged_messages(channel, '🤖'))
                    server_prompt_messages.extend(
                        await DiscordContentMessage.from_discord_message(message) for message in
                        await channel.pins())
            session.add(ContextSystemPrompt(
                server_id=discord_server.id,
                category_id=category.id,
                prompt_messages="\n".join(category_prompts)
            ))
            for channel in category.text_channels:
                discord_category.channels.append(channel.id)
                channel_prompts = copy(category_prompts)
                discord_channel = ChannelData(name=channel.name,
                                              id=channel.id,
                                              server_name=channel.guild.name,
                                              server_id=channel.guild.id,
                                              category_name=channel.category.name if channel.category else None,
                                              category_id=channel.category.id if channel.category else None,
                                              threads=[]
                                              )
                channel_prompts.append(channel.topic)

                channel_prompts.extend([await DiscordContentMessage.from_discord_message(message) for message in
                                        await channel.pins()])
                session.add(ContextSystemPrompt(
                    server_id=discord_server.id,
                    category_id=category.id,
                    channel_id=channel.id,
                    prompt_messages="\n".join(channel_prompts)
                ))

                for thread in channel.threads:
                    discord_channel.threads.append(thread.id)

                    discord_thread = DiscordThread(name=thread.name,
                                                   id=thread.id,
                                                   channel_name=thread.parent.name,
                                                   channel_id=thread.parent.id,
                                                   messages=[]
                                                   )

                    async for message in thread.history(limit=None, oldest_first=True):
                        if message.content == '' and len(message.attachments) == 0:
                            continue
                        if message.content.startswith('~'):
                            continue
                        update_latest_message_datetime(message.created_at)
                        discord_thread.messages.append(message.id)
                        discord_message = DiscordMessage(id=discord_message.id,
                                                         name=f"message-{discord_message.id}",
                                                         channel_id=discord_message.channel_id,
                                                         channel_name=discord_message.channel_name,
                                                         author_id=discord_message.author.id,
                                                         is_bot=discord_message.author.bot,
                                                         content=discord_message.clean_content,
                                                         jump_url=discord_message.jump_url,
                                                         attachments=[await extract_attachment_text(attachment) for
                                                                      attachment in
                                                                      discord_message.attachments],
                                                         timestamp=discord_message.created_at.isoformat(),
                                                         reactions=[reaction.emoji for reaction in
                                                                    discord_message.reactions],
                                                         parent_message_id=discord_message.reference.message_id if discord_message.reference else None

                                                         )

                        discord_thread.messages.append(discord_message.id)
                        session.add(discord_message)
                    session.add(discord_thread)
                session.add(discord_channel)
            session.add(discord_category)
        session.add(discord_server)
        session.commit()

