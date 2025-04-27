from typing import Optional

import aiohttp
import discord
from sqlalchemy import Column, Index, JSON, Text
from sqlmodel import Field, Relationship, Session, SQLModel

from skellybot_analysis.db.db_models.db_base_sql_model import BaseSQLModel
from skellybot_analysis.models.context_route_model import ContextRoute


class UserThread(SQLModel, table=True):
    """Association table for the many-to-many relationship between users and threads."""
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    user_name: Optional[str] = Field(index=True)
    thread_id: int = Field(foreign_key="thread.id", primary_key=True)
    thread_name: Optional[str] = Field(index=True)

    @classmethod
    def get_create_or_update(cls, session: Session, user_id: int, thread_id: int, user_name: str | None = None,
                             thread_name: str | None = None) -> "UserThread":
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
    server_id: int = Field(index=True)
    server_name: str = Field(index=True)
    category_id: Optional[int] = Field(index=True, default=None)
    category_name: Optional[str] = Field(index=True, default=None)
    channel_id: int = Field(index=True)
    channel_name: str = Field(index=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    # owner_name: str = Field(index=True)
    # Relationships
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
    )
    thread_id: Optional[int] = Field(default=None, index=True, foreign_key="thread.id")
    channel_id: Optional[int] = Field(default=None, index=True)

    # Relationships
    thread: Optional["Thread"] = Relationship(back_populates="messages")
    author: "User" = Relationship(back_populates="messages")
    parent_message: Optional["Message"] = Relationship(
    sa_relationship_kwargs = {
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
                             session: Session | None = None, ):
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
                                        parent_message_id=int(discord_message.reference.message_id) if discord_message.reference else None
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


    def as_full_text(self, with_names: bool = False) -> str:
        """
        Get the full text of the message.
        """
        content = ""
        if with_names:
            if self.is_bot:
                content += "- **BOT**: "
            else:
                content += "- **HUMAN**: "
            content += f"{self.content}\n\n"
        if self.attachments:
            content += "\n\nBEGIN ATTACHMENTS:\n\n"
            content += "\n\n".join(self.attachments)
            content += "\n\nEND ATTACHMENTS\n\n"
        return content


class ContextSystemPrompt(BaseSQLModel, table=True):
    """Represents a prompt for a given context"""

    system_prompt: str = Field(sa_column=Column(Text))

    context_route_ids: str = Field(index=True)  # `server_id`/`category_id`/`channel_id`
    context_route_names: str = Field(index=True)  # `server_name`/`category_name`/`channel_name`
    server_id: int = Field(index=True)
    server_name: str = Field(index=True)

    category_id: Optional[int] = Field(default=None, index=True)
    category_name: Optional[str] = Field(default=None, index=True)

    channel_id: Optional[int] = Field(default=None, index=True)
    channel_name: Optional[str] = Field(default=None, index=True)

    @classmethod
    def from_context(cls,
                     session: Session,
                     system_prompt: str,
                     context_route: ContextRoute,
                     ):
        """
        Create a ContextSystemPrompt from a context.
        """
        return cls.get_create_or_update(session=session,
                                        db_id=context_route.id,
                                        context_route_ids=context_route.ids,
                                        context_route_names=context_route.names,
                                        server_id=context_route.server_id,
                                        category_id=context_route.category_id,
                                        channel_id=context_route.channel_id,
                                        server_name=context_route.server_name,
                                        category_name=context_route.category_name,
                                        channel_name=context_route.channel_name,
                                        system_prompt=system_prompt)


class User(BaseSQLModel, table=True):
    """Represents a  user."""
    is_bot: bool

    # Relationships
    messages: list[Message] = Relationship(back_populates="author")
    threads: list[Thread] = Relationship(
        back_populates="users",
        link_model=UserThread
    )
    profile: Optional["UserProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )
