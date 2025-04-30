from datetime import datetime
from typing import Any

import discord
import numpy as np
from pydantic import BaseModel, model_validator, computed_field

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

    @model_validator(mode='before')
    @classmethod
    def handle_nan_values(cls, data: Any) -> Any:
        """Convert NaN values to appropriate defaults based on field types"""
        if isinstance(data, dict):
            for field_name, value in list(data.items()):
                # Handle NaN values
                if isinstance(value, float) and np.isnan(value):
                    field_info = cls.model_fields.get(field_name)
                    if field_info:
                        if field_info.annotation == str or str in getattr(field_info.annotation, "__args__", []):
                            data[field_name] = "none"
                        elif field_info.annotation == int or int in getattr(field_info.annotation, "__args__", []):
                            data[field_name] = -1
                        else:
                            data[field_name] = None
        return data
class ThreadModel(DataframeModel):
    thread_id: ThreadId
    thread_name: str
    server_id: ServerId
    server_name: str
    category_id: CategoryId|None = -1
    category_name: str|None = "none"
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
    category_id: CategoryId|None = -1
    category_name: str = "none"
    channel_id: ChannelId = -1
    channel_name: str = "none"


class MessageModel(DataframeModel):
    message_id: MessageId
    bot_message: bool
    content: str
    author_id: UserId
    jump_url: str

    parent_message_id: MessageId|None = -1

    server_id: ServerId
    server_name: str
    channel_id: ChannelId
    channel_name: str

    category_id: CategoryId|None = -1
    category_name: str = "none"
    thread_id: ThreadId|None = -1
    thread_name: str = "none"

    timestamp: datetime
    attachments:str|None = "none"


    @computed_field
    def full_content(self) -> str:
        if not self.attachments or self.attachments == "none":
            if not self.content or self.content == "none":
                return ""
            return self.content
        if not self.content or self.content == "none":
            return self.attachments

        return self.content + "\n\n" + self.attachments


    @classmethod
    async def from_discord_message(cls, msg:discord.Message, thread:discord.Thread|None=None) -> "MessageModel":
        """
        Create a MessageModel from a discord message.
        """

        return cls(
            message_id=msg.id,
            bot_message=msg.author.bot,
            content=msg.content if msg.content else "none",
            author_id=msg.author.id,
            jump_url=msg.jump_url,
            parent_message_id=msg.reference.message_id if msg.reference else -1,
            server_id=msg.guild.id,
            server_name=msg.guild.name,
            category_id=msg.channel.category.id if msg.channel.category else -1,
            category_name=msg.channel.category.name if msg.channel.category else "none",
            channel_id=msg.channel.id,
            channel_name=msg.channel.name,
            thread_id=thread.id if thread else -1,
            thread_name=thread.name if thread else "none",
            timestamp=msg.created_at,
            attachments="\n".join(await extract_attachments_from_discord_message(msg.attachments)) if msg.attachments else "none",
        )