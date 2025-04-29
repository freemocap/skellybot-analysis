import enum
from datetime import datetime

import discord
from pydantic import BaseModel, Field

from skellybot_analysis.utilities.extract_attachements_from_discord_message import \
    extract_attachments_from_discord_message

ServerId = int
CategoryId = int # using `-1` for None so its saves/loads easier
ChannelId = int
ThreadId = int
MessageId = int
ContextId = int  # hash(*[...context_ids]),

UserId = int


class DataframeModel(BaseModel):

    @classmethod
    def df_filename(cls) -> str:
        return cls.__name__.lower().replace("model", "s.csv")


class ThreadModel(DataframeModel):
    thread_id: ThreadId
    thread_name: str
    server_id: ServerId
    server_name: str
    category_id: CategoryId = -1
    category_name: str = "none"
    channel_id: ChannelId
    channel_name: str

    owner_id: UserId

    jump_url: str

    created_at: datetime


class UserModel(DataframeModel):
    user_id: UserId
    server_id: ServerId
    is_bot: bool
    joined_at: datetime


class ContextPromptModel(DataframeModel):
    context_id: ContextId
    server_id: ServerId
    server_name: str
    prompt_text: str
    category_id: CategoryId = -1
    category_name: str = "none"
    channel_id: ChannelId = -1
    channel_name: str = "none"


class MessageModel(DataframeModel):
    message_id: MessageId
    bot_message: bool
    content: str
    author_id: UserId
    jump_url: str

    parent_message_id: MessageId = -1

    server_id: ServerId
    server_name: str
    channel_id: ChannelId
    channel_name: str

    category_id: CategoryId = -1
    category_name: str = "none"
    thread_id: ThreadId = -1
    thread_name: str = "none"

    timestamp: datetime
    attachments:str = "none"

    @property
    def full_content(self):
        if self.attachments == "none":
            return self.content

        return self.content + "\n" + self.attachments

    @classmethod
    async def from_discord_message(cls, msg:discord.Message):
        """
        Create a MessageModel from a discord message.
        """
        return cls(
            message_id=msg.id,
            bot_message=msg.author.bot,
            content=msg.content,
            author_id=msg.author.id,
            jump_url=msg.jump_url,
            parent_message_id=msg.reference.message_id if msg.reference else -1,
            server_id=msg.guild.id,
            server_name=msg.guild.name,
            category_id=msg.channel.category.id if msg.channel.category else -1,
            category_name=msg.channel.category.name if msg.channel.category else "none",
            channel_id=msg.channel.id,
            channel_name=msg.channel.name,
            thread_id=msg.thread.id if msg.thread else -1,
            thread_name=msg.thread.name if msg.thread else "none",
            timestamp=msg.created_at,
            attachments="\n".join(await extract_attachments_from_discord_message(msg.attachments)) if msg.attachments else "none",
        )