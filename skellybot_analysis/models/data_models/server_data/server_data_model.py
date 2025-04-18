from datetime import datetime
from typing import Optional, Any

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, CheckConstraint, Index, JSON, Text


class DiscordBaseSQLModel(SQLModel):
    """Base model for all Discord entities with common fields."""
    id: int = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        # Ensure SQLModel serializes datetime objects correctly
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class DiscordServer(DiscordBaseSQLModel, table=True):
    """Represents a Discord server (guild)."""
    # Use proper relationship configuration
    categories: list["DiscordCategory"] = Relationship(
        back_populates="server",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class DiscordCategory(DiscordBaseSQLModel, table=True):
    """Represents a category in a Discord server."""
    server_id: int = Field(foreign_key="server.id", index=True)

    # Relationships
    server: DiscordServer = Relationship(back_populates="categories")
    channels: list["DiscordChannel"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class DiscordChannel(DiscordBaseSQLModel, table=True):
    """Represents a text channel in a Discord server."""
    category_id: int = Field(foreign_key="category.id", index=True)

    # Relationships
    category: DiscordCategory = Relationship(back_populates="channels")
    threads: list["Thread"] = Relationship(
        back_populates="channel",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    messages: list["DiscordMessage"] = Relationship(
        back_populates="channel",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class DiscordMessage(DiscordBaseSQLModel, table=True):
    """Represents a message in a Discord channel or thread."""
    content: str = Field(sa_column=Column(Text))
    author_id: int = Field(foreign_key="user.id", index=True)
    is_bot: bool = Field(index=True)
    jump_url: str

    # Store as proper JSON type instead of string
    attachments: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    reactions: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Foreign keys
    parent_message_id: Optional[int] = Field(
        default=None,
        foreign_key="message.id",
        sa_column_kwargs={"name": "parent_message_id"}
    )
    thread_id: Optional[int] = Field(default=None, foreign_key="thread.id", index=True)
    channel_id: Optional[int] = Field(default=None, foreign_key="channel.id", index=True)

    # Relationships
    thread: Optional["Thread"] = Relationship(back_populates="messages")
    channel: Optional["DiscordChannel"] = Relationship(back_populates="messages")
    author: "User" = Relationship(back_populates="messages")
    parent_message: Optional["DiscordMessage"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "DiscordMessage.id",
            "foreign_keys": "DiscordMessage.parent_message_id",
            "overlaps": "messages,parent_message"
        }
    )

    # Add proper table constraints for data integrity
    __table_args__ = (
        CheckConstraint(
            "(thread_id IS NOT NULL AND channel_id IS NULL) OR "
            "(thread_id IS NULL AND channel_id IS NOT NULL)",
            name="message_parent_check"
        ),
        Index("idx_message_created_at", "created_at"),
    )


class UserThread(SQLModel, table=True):
    """Association table for the many-to-many relationship between users and threads."""
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    thread_id: int = Field(foreign_key="thread.id", primary_key=True)
    joined_at: datetime = Field(default_factory=datetime.now)


class DiscordThread(DiscordBaseSQLModel, table=True):
    """Represents a thread in a Discord channel."""
    channel_id: int = Field(foreign_key="channel.id", index=True)

    # Relationships
    channel: DiscordChannel = Relationship(back_populates="threads")
    messages: list["DiscordMessage"] = Relationship(
        back_populates="thread",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    users: list["User"] = Relationship(
        back_populates="threads",
        link_model=UserThread
    )


class User(DiscordBaseSQLModel, table=True):
    """Represents a Discord user."""
    is_bot: bool = Field(default=False, index=True)

    # Relationships
    messages: list["DiscordMessage"] = Relationship(back_populates="author")
    threads: list["Thread"] = Relationship(
        back_populates="users",
        link_model=UserThread
    )

class ContextSystemPrompt(DiscordBaseSQLModel, table=True):
    """Represents a prompt for a given context"""
    server_id: int = Field(foreign_key="server.id", primary_key=True)
    category_id: Optional[int] = Field(foreign_key="category.id", primary_key=True)
    channel_id: Optional[int] = Field(foreign_key="channel.id", primary_key=True)
    thread_id: Optional[int] = Field(foreign_key="thread.id", primary_key=True)
    system_prompt: Optional[str] = None