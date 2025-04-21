from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar

import aiohttp
import discord
from sqlalchemy import Column, Index, JSON, Text
from sqlmodel import SQLModel, Field, Relationship, Session

from skellybot_analysis.utilities.sanitize_filename import sanitize_name

# Define TypeVar T bound to BaseSQLModel
T = TypeVar('T', bound='BaseSQLModel')


class BaseSQLModel(SQLModel):
    """Base model for all  entities with common fields."""
    id: int = Field(primary_key=True)
    name: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
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
            if flush: session.flush()

        return instance


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
    user_name: str = Field(index=True)
    thread_id: int = Field(foreign_key="thread.id", primary_key=True)
    thread_name: str = Field(index=True)
    joined_at: datetime = Field(default_factory=datetime.now)


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


class User(BaseSQLModel, table=True):
    """Represents a  user."""
    is_bot: bool

    # Relationships
    messages: list["Message"] = Relationship(back_populates="author")
    threads: list["Thread"] = Relationship(
        back_populates="users",
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
    async def from_discord_message(cls: Type[T],
                                   session: Session,
                                   discord_message: discord.Message):

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
    def from_context(cls: Type[T],
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


class ServerObjectAiAnalysis(SQLModel, table=True):
    """Represents an AI analysis of a server object"""

    context_route: str = Field(primary_key=True, index=True)  # `server_id`/`category_id`/`channel_id`/`thread_id`
    context_route_names: str = Field(index=True)  # `server_name`/`category_name`/`channel_name`/`thread_name`

    server_id: int = Field(foreign_key="server.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    channel_id: Optional[int] = Field(default=None, foreign_key="channel.id")
    thread_id: Optional[int] = Field(default=None, foreign_key="thread.id")

    server_name: str
    category_name: Optional[str]
    channel_name: Optional[str]
    thread_name: Optional[str]

    base_text: str = Field(description="The text this analysis is based on", sa_column=Column(Text))

    title_slug: str = Field(
        description="The a descriptive title of the text, will be used as the H1 header, the filename slug, and the URL slug. It should be short (only a few words) and provide a terse preview of the basic content of the full text, it should include NO colons")
    extremely_short_summary: str = Field(description="An extremely short 6-10 word summary of the text")
    very_short_summary: str = Field(description="A very short one sentence summary of the text")
    short_summary: str = Field(description="A short (2-3 sentence) summary of the text")
    highlights: str = Field(
        description="A (comma-separated string) list of the 5-10 most important points of the text, formatted as a bulleted list")
    detailed_summary: str = Field(
        description="An exhaustively thorough and detailed summary of the major points of this text in markdown bulleted outline format, like `* point 1\n* point 2\n* point 3` etc. Do not include conversational aspects such as 'the human greets the ai' and the 'ai responds with a greeting', only include the main contentful components of the text.")
    tags: str = Field(
        description="A (comma separated string) list of #tags that describe the content of the text, formatted as comma separated #lower-kabob-case. These should be like topic tags that can be used to categorize the text within a larger collection of texts. Ignore conversational aspects (such as '#greetings', '#farewells', '#thanks', etc.).  These should almost always be single word, unless the tag is a multi-word phrase that is commonly used as a single tag, in which case it should be hyphenated. For example, '#machine-learning, #python, #oculomotor-control,#neural-networks, #computer-vision', but NEVER things like '#computer-vision-conversation', '#computer-vision-questions', etc.")

    created_at: datetime = Field(default_factory=datetime.now)
    @property
    def safe_context_route(self) -> str:
        """
        Return a safe context route for the analysis.
        """
        cr = f"{sanitize_name(self.server_name)}-{self.server_id}/".lower().strip()
        if self.category_id:
            cr += f"{sanitize_name(self.category_name)}-{self.category_id}/".lower().strip()
        if self.channel_id:
            cr += f"{sanitize_name(self.channel_name)}-{self.channel_id}/".lower().strip()
        if self.thread_id:
            cr += f"{sanitize_name(self.thread_name)}-{self.thread_id}/".lower().strip()
        return cr

    @property
    def title(self):
        return self.title_slug.replace("-", " ").title()
    @property
    def filename(self, extension="md"):
        if not extension.startswith("."):
            extension = "." + extension
        return sanitize_name(self.title_slug.lower()) + f"{extension}"


    @property
    def tags_list(self):
        tags_list = self.tags.split(",")
        clean_tags = []
        for tag in tags_list:
            tag.strip()
            if not tag.startswith("#"):
                tag = "#" + tag
            tag.replace(" ", "-")
            tag = tag.replace("# ", "#")
            tag = tag.replace("##", "#")
            tag = tag.replace("###", "#")
            clean_tags.append(tag)
        return clean_tags

    @property
    def tags_string(self):
        return "\n".join(self.tags_list)

    @property
    def backlinks(self):
        bl = []
        for thing in self.tags_list:
            thing = f"[[{thing}]]"
            bl.append(thing)
        return "\n".join(bl)


    @property
    def full_text(self):
        return f"""
# {self.title}\n\n
> context route: {self.safe_context_route}\n\n
## Extremely Short Summary\n\n
{self.extremely_short_summary}\n\n
## Highlights\n
{self.highlights}\n\n
## Very Short Summary\n
{self.very_short_summary}\n\n
## Short Summary\n
{self.short_summary}\n\n
## Detailed Summary\n
{self.detailed_summary}\n\n
## Tags\n
{self.tags_string}\n\n
## Backlinks\n
{self.backlinks}\n\n
__
## Full Content Text\n
{self.base_text}\n\n
__
        """

    def save_as_markdown(self, base_folder: str):
        save_path = Path(base_folder) / self.safe_context_route
        save_path.mkdir(parents=True, exist_ok=True)

        with open(str(save_path / f"{self.filename}"), 'w', encoding='utf-8') as f:
            f.write(self.full_text)
