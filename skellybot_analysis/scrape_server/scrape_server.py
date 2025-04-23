import logging
from copy import copy

import discord
from sqlalchemy.engine import Engine
from sqlmodel import Session

from skellybot_analysis.models.context_route import ContextRoute
from skellybot_analysis.models.server_db_models import Thread, Message, UserThread, Server, \
    ContextSystemPrompt, Channel, Category, User
from skellybot_analysis.scrape_server.scrape_utils import update_latest_message_datetime, get_prompts_from_channel, \
    MINIMUM_THREAD_MESSAGE_COUNT

logger = logging.getLogger(__name__)


async def scrape_server(target_server: discord.Guild,
                        db_engine: Engine) -> None:
    logger.info(f'Successfully connected to the guild: {target_server.name} (ID: {target_server.id})')
    all_discord_threads = []
    with Session(db_engine) as session:
        try:
            db_server, server_prompt_messages = await db_process_server(session=session,
                                                                        target_server=target_server)
            if not db_server:
                logger.error(
                    f"Failed to process server: {target_server.name} (ID: {target_server.id}) - server not found")
                raise ValueError("Server not found in the database")

            # Process categories
            channels = await target_server.fetch_channels()
            for category in [channel for channel in channels if isinstance(channel, discord.CategoryChannel)]:
                if not category.text_channels:
                    logger.info(f"Skipping empty category: {category.name} (ID: {category.id})")
                    continue
                try:
                    db_category, category_prompts = await db_process_category(session=session,
                                                                              category=category,
                                                                              server_prompt_messages=server_prompt_messages,
                                                                              target_server=target_server)
                    if not db_category:
                        logger.error(
                            f"Failed to process category: {category.name} (ID: {category.id}) - category not found")
                        raise ValueError("Category not found in the database")
                    db_server.categories.append(db_category)
                except discord.errors.Forbidden as e:
                    logger.warning(
                        f"Failed to access category {category.name} (ID: {category.id}): {str(e)} - skipping")
                    continue

                logger.info(f"✅ Added category: {db_category.name} (ID: {db_category.id})")

                for channel in category.text_channels:
                    if not isinstance(channel, discord.TextChannel):
                        continue
                    channel_threads = await get_channel_threads(channel=channel)
                    if not channel_threads:
                        logger.info(f"No chat threads found in: {channel.name} (ID: {channel.id}) - skipping")
                        continue
                    try:
                        db_channel, channel_prompts = await db_process_channel(session=session,
                                                                               context_prompts=category_prompts,
                                                                               channel=channel,
                                                                               )
                        if not db_channel:
                            logger.error(
                                f"Failed to process channel: {channel.name} (ID: {channel.id}) - channel not found")
                            raise ValueError("Channel not found in the database")
                        channel_threads = await get_channel_threads(channel=channel)
                        db_category.channels.append(db_channel)
                        logger.info(f"✅ Added channel: {db_channel.name} (ID: {db_channel.id})")

                    except discord.errors.Forbidden as e:
                        logger.warning(
                            f"Failed to access channel {channel.name} (ID: {channel.id}): {str(e)} - skipping")
                        continue



                    for thread in channel_threads:
                        all_discord_threads.append(thread)
                        db_thread = await db_process_thread(session=session,
                                                            thread=thread)
                        if not db_thread:
                            logger.info(f"Skipping thread {thread.name} (ID: {thread.id}) for being empty or too short.")
                            continue
                        db_channel.threads.append(db_thread)
            session.commit()
            for discord_thread in all_discord_threads:
                await create_user_thread_associations(session=session,
                                                      thread=discord_thread)

        except Exception as e:
            session.rollback()
            logger.error(f"Critical error during scraping: {str(e)}", exc_info=True)
            raise
        # Final commit to ensure everything is saved
        session.commit()
        logger.info("✅ All data has been committed to the database")


async def get_channel_threads(channel: discord.TextChannel) -> list[discord.Thread]:
    channel_threads = channel.threads
    # get archived (i.e. 'timed out'/'inactive') threads
    async for thread in channel.archived_threads(limit=None):
        channel_threads.append(thread)
    return channel_threads


async def db_process_server(session: Session,
                            target_server: discord.Guild) -> tuple[Server, list[str]]:
    server_prompt_messages: list[str] = []
    db_server = Server.get_create_or_update(session=session,
                                            db_id=target_server.id,
                                            name=target_server.name,
                                            categories=[],
                                            channels=[], )
    session.flush()
    logger.info(f"✅ Added server record: {target_server.name} (ID: {target_server.id})")

    # Process server-level prompts/channels first
    channels = await target_server.fetch_channels()
    for channel in channels:
        if not isinstance(channel, discord.TextChannel):
            continue
        if not channel.category:
            if "bot" in channel.name or "prompt" in channel.name:
                logger.info(f"Extracting server-level prompts from channel: {channel.name}")
                server_prompt_messages.extend(
                    await get_prompts_from_channel(channel=channel, prompt_tag_emoji="🤖"))

            await db_process_channel(session=session,
                                     context_prompts=server_prompt_messages,
                                     channel=channel,
                                     )
    if server_prompt_messages:
        ContextSystemPrompt.from_context(session=session,
                                         system_prompt="\n".join(server_prompt_messages),
                                         context_route=ContextRoute(server_id=target_server.id,
                                                                    server_name=target_server.name, )
                                         )
        logger.info(f"✅ Added server-level system prompt")
    return db_server, server_prompt_messages


async def db_process_category(session: Session,
                              category: discord.CategoryChannel,
                              server_prompt_messages: list[str],
                              target_server: discord.Guild) -> tuple[Category, list[str]]:
    category_prompts: list[str] = copy(server_prompt_messages)

    # Process category-level prompts
    for channel in category.text_channels:
        if 'bot' in channel.name or 'prompt' in channel.name:
            category_prompts.extend(
                await get_prompts_from_channel(channel=channel, prompt_tag_emoji="🤖"))

    db_category = Category.get_create_or_update(session=session,
                                                db_id=category.id,
                                                name=category.name,
                                                server_name=target_server.name,
                                                server_id=target_server.id,
                                                channels=[]
                                                )
    ContextSystemPrompt.from_context(session=session,
                                     system_prompt="\n".join(category_prompts),
                                     context_route=ContextRoute(server_id=target_server.id,
                                                                server_name=target_server.name,
                                                                category_id=category.id,
                                                                category_name=category.name, )
                                     )
    return db_category, category_prompts


async def db_process_channel(session: Session,
                             context_prompts: list[str],
                             channel: discord.TextChannel,
                             ) -> tuple[Channel, list[str]] :
    channel_prompts = copy(context_prompts)
    channel_prompts.extend(await get_prompts_from_channel(channel=channel))

    db_channel = Channel.get_create_or_update(session=session,
                                              db_id=channel.id,
                                              name=channel.name,
                                              server_name=channel.guild.name,
                                              server_id=channel.guild.id,
                                              category_name=channel.category.name if channel.category else 'top-level',
                                              category_id=channel.category.id if channel.category else 0,
                                              threads=[]
                                              )
    ContextSystemPrompt.from_context(session=session,
                                     system_prompt="\n".join(channel_prompts),
                                     context_route=ContextRoute(server_id=channel.guild.id,
                                                                server_name=channel.guild.name,
                                                                category_id=channel.category.id if channel.category else 0,
                                                                category_name=channel.category.name if channel.category else 'top-level',
                                                                channel_id=channel.id,
                                                                channel_name=channel.name, )
                                     )
    return db_channel, channel_prompts


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
                                            channel_name=thread.parent.name,
                                            channel_id=thread.parent.id,
                                            owner_id=thread.owner_id,
                                            owner_name=thread.owner.name,
                                            messages=[]
                                            )
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


async def create_user_thread_associations(session: Session, thread: discord.Thread):
    try:
        # Get the thread members

        members = await thread.fetch_members()
        members = set([thread.owner] + members)
        if len(members) == 0:
            logger.warning(f"No members found for thread {thread.name} (ID: {thread.id})")

        for member in members:
            # Get or create the user
            discord_user = await thread.guild.fetch_member(member.id)
            user = User.get_create_or_update(session=session,
                                             db_id=discord_user.id,
                                             name=discord_user.name,
                                             is_bot=discord_user.bot,
                                             )

            # Create the association between user and thread
            user_thread = UserThread.get_create_or_update(session=session,
                                                          user_id=user.id,
                                                          user_name=user.name,
                                                          thread_id=thread.id,
                                                          thread_name=thread.name,
                                                          )

            # Add the association to the session
            session.add(user_thread)
            logger.info(
                f"✅ Added user-thread associations for thread: {thread.name} (ID: {thread.id}) and user: {user.name} (ID: {user.id})")
        session.commit()
    except discord.errors.Forbidden:
        logger.warning(f"Cannot access members for thread {thread.name} (ID: {thread.id})")
    except Exception as e:
        logger.error(f"Error getting members for thread {thread.name}: {str(e)}")
        raise
