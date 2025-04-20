from datetime import datetime
from typing import Optional, Type, TypeVar

import aiohttp
import discord
from sqlalchemy import Column, Index, JSON, Text
from sqlmodel import SQLModel, Field, Relationship, Session

# Define TypeVar T bound to BaseSQLModel
T = TypeVar('T', bound='BaseSQLModel')


class BaseSQLModel(SQLModel):
    """Base model for all  entities with common fields."""
    id: int = Field(primary_key=True)
    name: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        # Ensure SQLModel serializes datetime objects correctly
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

    @classmethod
    def get_create_or_update(cls: Type[T],
                             session: Session,
                             db_id: int | str,
                             flush: bool = True,
                             **kwargs) -> T:
        """
        Get an existing record by id, create a new one if it doesn't exist,
        or update it if provided fields differ from current values.

        Args:
            session: SQLModel Session object
            db_id: Primary key value in the database
            flush: Whether to flush the session after adding the instance
            **kwargs: Fields to set/update on the model instance

        Returns:
            The model instance (either existing, new, or updated)
        """
        instance = session.get(cls, db_id)

        if not instance:
            # Create new instance if it doesn't exist
            instance = cls(id=db_id, **kwargs)
            session.add(instance)
            session.flush() if flush else None
            return instance

        # Check if any fields need updating
        needs_update = False
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None and getattr(instance, key) != value:
                setattr(instance, key, value)
                needs_update = True

        if needs_update:
            session.add(instance)
            session.flush() if flush else None

        return instance


class Server(BaseSQLModel, table=True):
    """Represents a  server (guild)."""
    # Use proper relationship configuration
    categories: list["Category"] = Relationship(
        back_populates="server",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    channels: list["Channel"] = Relationship(
        back_populates="server",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Category(BaseSQLModel, table=True):
    """Represents a category in a  server."""
    server_id: int = Field(foreign_key="server.id", index=True)

    # Relationships
    server: Server = Relationship(back_populates="categories")
    channels: list["Channel"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Channel(BaseSQLModel, table=True):
    """Represents a text channel in a  server."""
    server_id: int = Field(foreign_key="server.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)

    # Relationships
    server: Server = Relationship(back_populates="channels")
    category: Category = Relationship(back_populates="channels")
    threads: list["Thread"] = Relationship(
        back_populates="channel",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    messages: list["Message"] = Relationship(
        back_populates="channel",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class UserThread(SQLModel, table=True):
    """Association table for the many-to-many relationship between users and threads."""
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    thread_id: int = Field(foreign_key="thread.id", primary_key=True)
    joined_at: datetime = Field(default_factory=datetime.now)


class Thread(BaseSQLModel, table=True):
    """Represents a thread in a  channel."""
    channel_id: int = Field(foreign_key="channel.id", index=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    # Relationships
    channel: Channel = Relationship(back_populates="threads")
    messages: list["Message"] = Relationship(
        back_populates="thread",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    users: list["User"] = Relationship(
        back_populates="threads",
        link_model=UserThread
    )


class User(BaseSQLModel, table=True):
    """Represents a  user."""
    is_bot: bool

    # Relationships
    messages: list["Message"] = Relationship(back_populates="author")
    threads: list["Thread"] = Relationship(
        back_populates="users",
        link_model=UserThread
    )


class ContextSystemPrompt(SQLModel, table=True):
    """Represents a prompt for a given context"""

    context_route: str = Field(primary_key=True)  # `server_id`/`category_id`/`channel_id`
    server_id: int = Field(foreign_key="server.id")
    category_id: Optional[int] = Field(foreign_key="category.id")
    channel_id: Optional[int] = Field(foreign_key="channel.id")
    system_prompt: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        # Ensure SQLModel serializes datetime objects correctly
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

    @classmethod
    def from_context(cls: Type[T],
                     session: Session,
                     system_prompt: str,
                     server_id: int,
                     category_id: int | None = None,
                     channel_id: int | None = None,
                     ):
        """
        Create a ContextSystemPrompt from a context.
        """

        context_route = f"{server_id}"
        if category_id is not None:
            context_route += f"/{category_id}"
        if channel_id is not None:
            context_route += f"/{channel_id}"

        instance = session.get(cls, context_route)

        if not instance:
            # Create new instance if it doesn't exist
            instance = cls(context_route=context_route,
                           server_id=server_id,
                           category_id=category_id,
                           channel_id=channel_id,
                           system_prompt=system_prompt)
            session.add(instance)
            session.flush()
            return instance

        # Update the system prompt if it has changed
        if instance.system_prompt != system_prompt:
            instance.system_prompt = system_prompt
            session.add(instance)
            session.flush()

        return instance


class Message(BaseSQLModel, table=True):
    """Represents a message in a  channel or thread."""
    content: str = Field(sa_column=Column(Text))
    is_bot: bool = Field(index=True)
    jump_url: str

    # Store as proper JSON type instead of string
    attachments: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    reactions: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Foreign keys
    author_id: int = Field(foreign_key="user.id", index=True)
    parent_message_id: Optional[int] = Field(
        default=None,
        foreign_key="message.id",
        sa_column_kwargs={"name": "parent_message_id"}
    )
    thread_id: Optional[int] = Field(default=None, foreign_key="thread.id", index=True)
    channel_id: Optional[int] = Field(default=None, foreign_key="channel.id", index=True)

    # Relationships
    thread: Optional["Thread"] = Relationship(back_populates="messages")
    channel: Optional["Channel"] = Relationship(back_populates="messages")
    author: "User" = Relationship(back_populates="messages")
    parent_message: Optional["Message"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "Message.id",
            "foreign_keys": "Message.parent_message_id",
            "overlaps": "messages,parent_message"
        }
    )

    # Add proper table constraints for data integrity
    __table_args__ = (
        Index("idx_message_created_at", "created_at"),
    )

    @classmethod
    async def from_discord_message(cls: Type[T],
                                   session: Session,
                                   discord_message: discord.Message):
        return cls.get_create_or_update(session=session,
                                        db_id=discord_message.id,
                                        name=f"message-{discord_message.id}",
                                        channel_id=discord_message.channel.id,
                                        channel_name=discord_message.channel.name,
                                        thread_id=discord_message.thread.id if discord_message.thread else 0,
                                        thread_name=discord_message.thread.name if discord_message.thread else 'channel-message',
                                        author_id=discord_message.author.id,
                                        is_bot=discord_message.author.bot,
                                        content=discord_message.clean_content,
                                        jump_url=discord_message.jump_url,
                                        attachments=await cls.extract_attachments(discord_message.attachments),
                                        timestamp=discord_message.created_at.isoformat(),
                                        reactions=[reaction.emoji for reaction in discord_message.reactions],
                                        parent_message_id=discord_message.reference.message_id if discord_message.reference else None
                                        )

    @staticmethod
    async def extract_attachments(attachments: list[discord.Attachment]|None) -> list[str]:
        """
        Extract the text from a discord attachment.
        """
        attachment_texts = []
        if not attachments:
            return attachment_texts

        for attachment in attachments:
            if attachment.content_type and 'text' in attachment.content_type:
                attachment_string = f"START [{attachment.filename}]({attachment.url})"
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            try:
                                attachment_string += await resp.text()
                            except UnicodeDecodeError:
                                attachment_string += await resp.text(errors='replace')
                attachment_string += f" END [{attachment.filename}]({attachment.url})"
                attachment_texts.append(attachment_string)
        return attachment_texts
