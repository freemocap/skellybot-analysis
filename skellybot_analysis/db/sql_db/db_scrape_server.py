import logging

import discord
from sqlalchemy.engine import Engine
from sqlmodel import Session

from skellybot_analysis.db.sql_db.sql_db_models.db_server_models import ContextSystemPrompt, Thread, User, Message
from skellybot_analysis.scrape_server.scrape_utils import get_prompts_from_channel, MINIMUM_THREAD_MESSAGE_COUNT, \
    update_latest_message_datetime
from skellybot_analysis.models.context_route_model import ContextRoute

logger = logging.getLogger(__name__)


async def scrape_server(target_server: discord.Guild, db_engine: Engine) -> None:
    logger.info(f'Successfully connected to the guild: {target_server.name} (ID: {target_server.id})')

    all_channels = await target_server.fetch_channels()
    text_channels = [channel for channel in all_channels if isinstance(channel, discord.TextChannel)]
    all_discord_threads: list[discord.Thread] = []
    for channel in text_channels:
        all_discord_threads.extend(await get_channel_threads(channel))

    with Session(db_engine) as session:
        try:
            await grab_context_prompts(session, target_server, text_channels)

            for thread in all_discord_threads:
                await db_process_thread(session=session,
                                        thread=thread)

            session.commit()
            # for thread in all_discord_threads:
            #     await create_user_thread_associations(session=session, thread=thread)
        except Exception as e:
            session.rollback()
            logger.error(f"Critical error during scraping: {str(e)}", exc_info=True)
            raise
        # Final commit to ensure everything is saved
        session.commit()
        logger.info("✅ All data has been committed to the database")


async def grab_context_prompts(session:Session,
                               target_server: discord.Guild,
                               text_channels: list[discord.TextChannel]) -> None:
    server_prompt = await get_server_prompt(session=session,
                                            target_server=target_server,
                                            text_channels=text_channels)
    category_prompt_messages = await get_category_prompts(server_prompt=server_prompt,
                                                          session=session,
                                                          target_server=target_server,
                                                          text_channels=text_channels)
    _ = await get_channel_prompts(session=session,
                                  text_channels=text_channels,
                                  server_prompt=server_prompt,
                                  category_prompt_messages=category_prompt_messages)


async def get_channel_prompts(session: Session,
                              text_channels: list[discord.TextChannel],
                              server_prompt: str,
                              category_prompt_messages: dict[int, str]) -> dict[int, str]:
    channel_prompts: dict[int, str] = {}
    for channel in text_channels:
        if not isinstance(channel, discord.TextChannel):
            continue
        channel_threads = await get_channel_threads(channel=channel)
        if not channel_threads:
            logger.info(f"No chat threads found in: {channel.name} (ID: {channel.id}) - skipping")
            continue
        base_prompt = category_prompt_messages.get(channel.category_id, server_prompt)
        channel_prompt = base_prompt + "\n".join(await get_prompts_from_channel(channel=channel))
        channel_prompts[channel.id] = channel_prompt
        ContextSystemPrompt.from_context(session=session,
                                         system_prompt=channel_prompt,
                                         context_route=ContextRoute(server_id=channel.guild.id,
                                                                    server_name=channel.guild.name,
                                                                    category_id=channel.category.id if channel.category else None,
                                                                    category_name=channel.category.name if channel.category else None,
                                                                    channel_id=channel.id,
                                                                    channel_name=channel.name,
                                                                    )
                                         )
        logger.info(f"✅ Added channel system prompt for channel: {channel.name} (ID: {channel.id})")

    return channel_prompts


async def get_category_prompts(server_prompt: str,
                               session: Session,
                               target_server: discord.Guild,
                               text_channels: list[discord.TextChannel]) -> dict[int, str]:
    category_prompt_messages: dict[int, str] = {}
    for channel in text_channels:
        if not channel.category:
            continue
        if "bot" in channel.name or "prompt" in channel.name or "instructions" in channel.name:
            logger.info(f"Extracting server-level prompts from channel: {channel.name}")
            category_prompt_messages[channel.category_id] = server_prompt + "\n".join(
                await get_prompts_from_channel(channel=channel, prompt_tag_emoji="🤖"))
            ContextSystemPrompt.from_context(
                session=session,
                system_prompt=category_prompt_messages[channel.category_id],
                context_route=ContextRoute(server_id=target_server.id,
                                           server_name=target_server.name,
                                           category_id=channel.category_id,
                                           category_name=channel.category.name,
                                           )
            )
            logger.info(
                f"✅ Added category system prompt for category: {channel.category.name} (ID: {channel.category.id})")
    return category_prompt_messages


async def get_server_prompt(session: Session,
                            target_server: discord.Guild,
                            text_channels: list[discord.TextChannel]) -> str:
    server_prompt = ""
    for channel in text_channels:
        if channel.category:
            continue
        if "bot" in channel.name or "prompt" in channel.name or "instructions" in channel.name:
            logger.info(f"Extracting server-level prompts from channel: {channel.name}")
            server_prompt += "\n".join(await get_prompts_from_channel(channel=channel, prompt_tag_emoji="🤖"))
    if server_prompt:
        ContextSystemPrompt.from_context(
            session=session,
            system_prompt=server_prompt,
            context_route=ContextRoute(server_id=target_server.id,
                                       server_name=target_server.name,
                                       )
        )
        logger.info(f"✅ Added server-level system prompt")
    return server_prompt


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


async def db_process_thread(session: Session,
                            thread: discord.Thread) -> Thread | None:
    message_count = 0
    thread_messages: list[discord.Message] = []
    async for message in thread.history(limit=None, oldest_first=True):
        thread_messages.append(message)

    if thread.name == '.' and all([message.author.bot for message in thread_messages]):
        logger.info(f"Thread {thread.name} (ID: {thread.id}) is empty or only has bot messages.")
        return None

    if len(thread_messages) < MINIMUM_THREAD_MESSAGE_COUNT:
        logger.info(f"Thread {thread.name} (ID: {thread.id}) has fewer than {MINIMUM_THREAD_MESSAGE_COUNT} messages.")
        return None

    User.get_create_or_update(session=session,
                              db_id=thread.owner.id,
                              name=thread.owner.name,
                              is_bot=thread.owner.bot)

    db_thread = Thread.get_create_or_update(session=session,
                                            db_id=thread.id,
                                            name=thread.name,
                                            server_id=thread.guild.id,
                                            server_name=thread.guild.name,
                                            category_id=thread.parent.category.id if thread.parent.category else None,
                                            category_name=thread.parent.category.name if thread.parent.category else None,
                                            channel_name=thread.parent.name,
                                            channel_id=thread.parent.id,
                                            owner_id=thread.owner_id,
                                            owner_name=thread.owner.name,
                                            messages=[]
                                            )
    session.commit()
    for discord_message in thread_messages:
        if not discord_message.content and len(discord_message.attachments) == 0:
            continue
        if discord_message.content.startswith('~'):
            continue
        update_latest_message_datetime(discord_message.created_at)

        User.get_create_or_update(session=session,
                                  db_id=discord_message.author.id,
                                  name=discord_message.author.name,
                                  is_bot=discord_message.author.bot)

        db_message = await Message.from_discord_message(session=session,
                                                        discord_message=discord_message)
        db_thread.messages.append(db_message)
        message_count += 1
    logger.info(
        f"✅ Added thread: {db_thread.name} (ID: {db_thread.id}) with {message_count} messages")

    return db_thread
