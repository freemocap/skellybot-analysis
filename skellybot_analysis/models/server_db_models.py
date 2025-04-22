from datetime import datetime
from typing import Optional

import aiohttp
import discord
from sqlalchemy import Column, Index, JSON, Text
from sqlmodel import SQLModel, Field, Relationship, Session

from skellybot_analysis.models.base_sql_model import BaseSQLModel


class Server(BaseSQLModel, table=True):
    """Represents a  server (guild)."""
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
    server_name: str = Field(index=True)
    # Relationships
    server: Server = Relationship(back_populates="categories")
    channels: list["Channel"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Channel(BaseSQLModel, table=True):
    """Represents a text channel in a  server."""
    server_id: int = Field(foreign_key="server.id", index=True)
    server_name: str = Field(index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    category_name: str = Field(index=True)

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
    user_name: Optional[str] = Field(index=True)
    thread_id: int = Field(foreign_key="thread.id", primary_key=True)
    thread_name: Optional[str] = Field(index=True)

    @classmethod
    def get_create_or_update(cls,session: Session, user_id: int, thread_id: int, user_name: str | None = None, thread_name: str | None = None) -> "UserThread":
        """
        Get or create a UserThread instance.
        """
        instance = session.get(UserThread, (user_id, thread_id))
        if not instance:
            instance = UserThread(user_id=user_id, thread_id=thread_id,
                                  user_name=user_name, thread_name=thread_name)
            session.add(instance)
            session.flush()

        # Update the instance with any additional kwargs
        needs_update = False
        if user_name and instance.user_name != user_name:
            instance.user_name = user_name
            needs_update = True
        if thread_name and instance.thread_name != thread_name:
            instance.thread_name = thread_name
            needs_update = True
        # Flush the session if needed
        if needs_update:
            session.add(instance)
            session.flush()

        return instance


class Thread(BaseSQLModel, table=True):
    """Represents a thread in a  channel."""
    channel_id: int = Field(foreign_key="channel.id", index=True)
    channel_name: str = Field(index=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    owner_name: str = Field(index=True)
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




class Message(BaseSQLModel, table=True):
    """Represents a message in a  channel or thread."""
    content: str = Field(sa_column=Column(Text))
    is_bot: bool = Field(index=True)
    jump_url: str
    timestamp: str = Field(description="Unix timestamp of the message creation time")

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
            "foreign_keys": "Message.parent_message_id"
        }
    )

    # Add  table constraints for data integrity
    __table_args__ = (
        Index("idx_message_created_at", "created_at"),
    )

    @classmethod
    async def from_discord_message(cls,
                                   discord_message: discord.Message,
                                   session: Session|None = None,):

        attachments = await cls.extract_attachments(discord_message.attachments)

        return cls.get_create_or_update(session=session,
                                        db_id=discord_message.id,
                                        name=f"message-{discord_message.id}",
                                        channel_id=discord_message.channel.id,
                                        channel_name=discord_message.channel.name,
                                        thread_id=discord_message.thread.id if discord_message.thread else None,
                                        thread_name=discord_message.thread.name if discord_message.thread else 'channel-message',
                                        author_id=discord_message.author.id,
                                        is_bot=discord_message.author.bot,
                                        content=discord_message.clean_content,
                                        jump_url=discord_message.jump_url,
                                        attachments=attachments if not discord_message.author.bot else [],
                                        timestamp=discord_message.created_at.isoformat(),
                                        reactions=[reaction.emoji for reaction in discord_message.reactions],
                                        parent_message_id=discord_message.reference.message_id if discord_message.reference else None
                                        )

    @staticmethod
    async def extract_attachments(attachments: list[discord.Attachment] | None) -> list[str]:
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

    def as_full_text(self) -> str:
        """
        Get the full text of the message.
        """
        full_text = f"{self.content}\n\n"
        if self.attachments:
            full_text += "\n\nBEGIN ATTACHMENTS:\n\n"
            full_text += "\n\n".join(self.attachments)
            full_text += "\n\nEND ATTACHMENTS\n\n"
        return full_text


class ContextSystemPrompt(SQLModel, table=True):
    """Represents a prompt for a given context"""

    system_prompt: str = Field(sa_column=Column(Text))

    context_route: str = Field(primary_key=True, index=True)  # `server_id`/`category_id`/`channel_id`
    context_route_names: str = Field(index=True)  # `server_name`/`category_name`/`channel_name`
    server_id: int = Field(foreign_key="server.id")
    server_name: str = Field(index=True)

    category_id: Optional[int] = Field(foreign_key="category.id")
    category_name: Optional[str] = Field(default=None, index=True)

    channel_id: Optional[int] = Field(foreign_key="channel.id")
    channel_name: Optional[str] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

    @classmethod
    def from_context(cls,
                     session: Session,
                     system_prompt: str,
                     server_id: int,
                     server_name: str,
                     category_id: int | None = None,
                     category_name: str | None = None,
                     channel_name: str | None = None,
                     channel_id: int | None = None,
                     ):
        """
        Create a ContextSystemPrompt from a context.
        """

        context_route = f"{server_id}"
        context_route_names = f"{server_name}"
        if category_id is not None:
            if category_name is None:
                raise ValueError("category_name must be provided if category_id is provided")
            context_route += f"/{category_id}"
            context_route_names += f"/{category_name}"
        if channel_id is not None:
            if channel_name is None:
                raise ValueError("channel_name must be provided if channel_id is provided")
            context_route += f"/{channel_id}"
            context_route_names += f"/{channel_name}"

        instance = session.get(cls, context_route)

        if not instance:
            instance = cls(context_route=context_route,
                           context_route_names=context_route_names,
                           server_id=server_id,
                           category_id=category_id,
                           channel_id=channel_id,
                           server_name=server_name,
                           category_name=category_name,
                           channel_name=channel_name,
                           system_prompt=system_prompt)
            # Create new instance if it doesn't exist
            session.add(instance)
            session.flush()
            return instance

        # Update the system prompt if it has changed
        if instance.system_prompt != system_prompt:
            instance.system_prompt = system_prompt
            # Note - names may change, id's will not
            instance.server_name = server_name
            instance.category_name = category_name
            instance.channel_name = channel_name
            instance.context_route_names = context_route_names
            session.add(instance)
            session.flush()

        return instance



