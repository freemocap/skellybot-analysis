from datetime import datetime
from typing import Optional

from sqlmodel import  SQLModel, Field, Relationship
from sqlalchemy import CheckConstraint, Index

class DiscordBaseSQLModel(SQLModel):
    id: int = Field(primary_key=True) #Discord assigned ID
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Server(DiscordBaseSQLModel, table=True):
    categories: list["Category"] = Relationship(back_populates="server")

class Category(DiscordBaseSQLModel, table=True):
    server_id: int = Field(foreign_key="server.id")
    server: Server = Relationship(back_populates="categories")
    channels: list["Channel"] = Relationship(back_populates="category")

class Channel(DiscordBaseSQLModel, table=True):
    category_id: int = Field(foreign_key="category.id")
    category: Category = Relationship(back_populates="channels")
    threads: list["Thread"] = Relationship(back_populates="channel")
    messages: list["Message"] = Relationship(back_populates="channel")



class Message(DiscordBaseSQLModel, table=True):
    content: str
    author_id: int = Field(foreign_key="user.id")
    is_bot: bool
    jump_url: str
    attachments: str  # JSON serialized list
    reactions: str  # JSON serialized list
    parent_message_id: Optional[int] = Field(
        default=None,
        foreign_key="message.id",  # References the message table's id column
        sa_column_kwargs={"name": "parent_message_id"}
    )
    thread_id: Optional[int] = Field(foreign_key="thread.id")
    channel_id: Optional[int] = Field(foreign_key="channel.id")

    # Relationships
    thread: Optional["Thread"] = Relationship(back_populates="messages")
    channel: Optional["Channel"] = Relationship(back_populates="messages")
    author: "User" = Relationship(back_populates="messages")
    parent_message: Optional["Message"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "Message.id",  # The parent message's ID we're referencing
            "foreign_keys": "Message.parent_message_id"  # Explicit foreign key mapping
        }
    )
    __table_args__ = (
        CheckConstraint(
            "(thread_id IS NOT NULL AND channel_id IS NULL) OR "
            "(thread_id IS NULL AND channel_id IS NOT NULL)",
            name="message_parent_check"
        ),
    )
class UserThread(SQLModel, table=True):
    user_id: int = Field(
        foreign_key="user.id",
        primary_key=True
    )
    thread_id: int = Field(
        foreign_key="thread.id",
        primary_key=True
    )

class Thread(DiscordBaseSQLModel, table=True):
    channel_id: int = Field(foreign_key="channel.id")
    channel: Channel = Relationship(back_populates="threads")
    messages: list["Message"] = Relationship(back_populates="thread")
    # Add the back-reference for the many-to-many relationship with users
    users: list["User"] = Relationship(
        back_populates="threads",
        link_model=UserThread
    )
class User(DiscordBaseSQLModel, table=True):
    is_bot: bool = False

    # Relationships
    messages: list["Message"] = Relationship(back_populates="author")
    threads: list["Thread"] = Relationship(
        back_populates="users",
        link_model=UserThread
    )
    __table_args__ = (
        Index("idx_user_is_bot", "is_bot"),
    )

