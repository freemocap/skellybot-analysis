import json
import logging
from datetime import datetime

import discord
from sqlmodel import select

from skellybot_analysis.models.data_models.discord_db.discord_sql_models import (
    Server, Category, Channel, Thread, Message, User, UserThread
)
from skellybot_analysis.scrape_server.sql_db_connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)

class DiscordSQLMapper:
    """Maps Discord objects directly to SQL database models."""


    @classmethod
    async def save_server(cls, discord_server: discord.Guild) -> Server:
        """Save a Discord server to the database or get an existing one."""
        with DatabaseConnectionManager.get_session() as session:
            # Check if server exists
            server = session.exec(select(Server).where(Server.id == discord_server.id)).first()

            if not server:
                # Create new server
                server = Server(
                    id=discord_server.id,
                    name=discord_server.name,
                    created_at=discord_server.created_at.isoformat()
                )
                session.add(server)
                session.commit()
                session.refresh(server)

        return server

    @classmethod
    async def save_category(cls, discord_category: discord.CategoryChannel, server_id: int) -> Category:
        """Save a Discord category to the database or get an existing one."""
        with DatabaseConnectionManager.get_session() as session:
            # Check if category exists
            category = session.exec(
                select(Category).where(Category.id == discord_category.id)
            ).first()

            if not category:
                # Create new category
                category = Category(
                    id=discord_category.id,
                    name=discord_category.name,
                    server_id=server_id,
                    created_at=discord_category.created_at.isoformat()
                )
                session.add(category)
                session.commit()
                session.refresh(category)

        return category

    @classmethod
    async def save_channel(cls, discord_channel: discord.TextChannel, category_id: int) -> Channel:
        """Save a Discord channel to the database or get an existing one."""
        with DatabaseConnectionManager.get_session() as session:
            # Check if channel exists
            channel = session.exec(
                select(Channel).where(Channel.id == discord_channel.id)
            ).first()

            if not channel:
                # Create new channel
                channel = Channel(
                    id=discord_channel.id,
                    name=discord_channel.name,
                    category_id=category_id,
                    created_at=discord_channel.created_at.isoformat()
                )
                session.add(channel)
                session.commit()
                session.refresh(channel)

        return channel

    @classmethod
    async def save_thread(cls, discord_thread: discord.Thread, channel_id: int) -> Thread:
        """Save a Discord thread to the database or get an existing one."""
        with DatabaseConnectionManager.get_session() as session:
            # Check if thread exists
            thread = session.exec(
                select(Thread).where(Thread.id == discord_thread.id)
            ).first()

            if not thread:
                # Create new thread
                thread = Thread(
                    id=discord_thread.id,
                    name=discord_thread.name,
                    channel_id=channel_id,
                    created_at=discord_thread.created_at.isoformat()
                )
                session.add(thread)
                session.commit()
                session.refresh(thread)

                # Save thread members
                for member in discord_thread.members:
                    # Make sure user is saved first
                    user = await cls.save_or_get_user(member)
                    # Create thread membership
                    user_thread = UserThread(
                        user_id=user.id,
                        thread_id=thread.id
                    )
                    session.add(user_thread)
                session.commit()

        return thread

    @classmethod
    async def save_message(cls,
                          discord_message: discord.Message,
                          channel_id: int,
                          thread_id: int|None = None,
                          parent_message_id: int|None = None) -> Message:
        """Save a Discord message to the database."""
        # First save the author
        author = await cls.save_or_get_user(discord_message.author)

        with DatabaseConnectionManager.get_session() as session:
            # Check if message exists
            message = session.exec(
                select(Message).where(Message.id == discord_message.id)
            ).first()

            if not message:
                # Create new message
                message = Message(
                    id=discord_message.id,
                    content=discord_message.content,
                    author_id=author.id,
                    is_bot=discord_message.author.bot,
                    jump_url=discord_message.jump_url,
                    attachments=cls.serialize_attachments(discord_message.attachments),
                    reactions=cls.serialize_reactions(discord_message.reactions),
                    thread_id=thread_id,
                    channel_id=channel_id,
                    parent_message_id=parent_message_id,
                    name=f"Message-{discord_message.id}",  # We need a name field as defined in DiscordBase
                    created_at=discord_message.created_at.isoformat()
                )
                session.add(message)
                session.commit()
                session.refresh(message)

        return message

    @staticmethod
    def serialize_attachments(attachments: list[discord.Attachment]) -> str:
        """Convert Discord attachments to JSON string."""
        return json.dumps([{
            'id': attachment.id,
            'filename': attachment.filename,
            'url': attachment.url,
            'size': attachment.size,
            'content_type': attachment.content_type
        } for attachment in attachments])

    @staticmethod
    def serialize_reactions(reactions: list[discord.Reaction]) -> str:
        """Convert Discord reactions to JSON string."""
        return json.dumps([{
            'emoji': str(reaction.emoji),
            'count': reaction.count
        } for reaction in reactions])

    @classmethod
    async def save_or_get_user(cls, discord_user: discord.User) -> User:
        """Save a Discord user to the database or get an existing one."""
        with DatabaseConnectionManager.get_session() as session:
            # Check if user exists
            user = session.exec(select(User).where(User.id == discord_user.id)).first()

            if not user:
                # Create new user
                user = User(
                    id=discord_user.id,
                    name=discord_user.name,
                    is_bot=discord_user.bot,
                    created_at=datetime.now().isoformat()
                )
                session.add(user)
                session.commit()
                session.refresh(user)

        return user