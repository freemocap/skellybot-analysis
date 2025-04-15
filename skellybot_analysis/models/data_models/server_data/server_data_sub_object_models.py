from datetime import datetime
from typing import List, Dict, Any, Optional

import aiohttp
import discord
from pydantic import Field, computed_field

from skellybot_analysis.models.data_models.data_object_model import DataObjectModel
from skellybot_analysis.models.data_models.server_data.server_context_route_model import ServerContextRoute
from skellybot_analysis.models.data_models.server_data.server_data_object_types_enum import ServerDataObjectTypes


class DiscordContentMessage(DataObjectModel):
    type: ServerDataObjectTypes = ServerDataObjectTypes.MESSAGE
    author_id: int
    is_bot: bool
    content: str = Field(default_factory=str,
                         description='The content of the message, as from `discord.message.clean_content`')
    jump_url: str = Field(default_factory=str,
                          description='The URL that links to the message in the Discord chat')
    attachments: List[str] = Field(default_factory=list,
                                   alias='Attachments',
                                   description='A list of text any (text) attachments in the message, wrapped in '
                                               '`START [filename](url) END [filename](url)`')
    timestamp: str = Field(default_factory=datetime.now().isoformat,
                           description='The timestamp of the message in ISO 8601 format')
    reactions: List[str] = Field(default_factory=list,
                                 description='A list of reactions to the message')
    parent_message_id: int | None = Field(default=None,
                                          description='The ID of the parent message, if this message is a reply')

    @computed_field
    @property
    def is_reply(self) -> bool:
        return self.parent_message_id is not None

    @classmethod
    async def from_discord_message(cls, discord_message: discord.Message):
        return cls(
            id=discord_message.id,
            name=f"message-{discord_message.id}",
            context_route=ServerContextRoute(
                server_name=discord_message.guild.name,
                server_id=discord_message.guild.id,
                category_name=discord_message.channel.category.name if discord_message.channel.category else None,
                category_id=discord_message.channel.category.id if discord_message.channel.category else None,
                channel_name=discord_message.channel.name,
                channel_id=discord_message.channel.id,
                thread_name=discord_message.thread.name if discord_message.thread else None,
                thread_id=discord_message.thread.id if discord_message.thread else None,
                message_id=discord_message.id
            ),

            author_id=discord_message.author.id,
            is_bot=discord_message.author.bot,
            content=discord_message.clean_content,
            jump_url=discord_message.jump_url,
            attachments=[await cls.extract_attachment_text(attachment) for attachment in discord_message.attachments],
            timestamp=discord_message.created_at.isoformat(),
            reactions=[reaction.emoji for reaction in discord_message.reactions],
            parent_message_id=discord_message.reference.message_id if discord_message.reference else None
        )

    @staticmethod
    async def extract_attachment_text(attachment: discord.Attachment) -> str:
        """
        Extract the text from a discord attachment.
        """
        attachment_string = f"START [{attachment.filename}]({attachment.url})"
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    try:
                        attachment_string += await resp.text()
                    except UnicodeDecodeError:
                        attachment_string += await resp.text(errors='replace')
        attachment_string += f" END [{attachment.filename}]({attachment.url})"
        return attachment_string

    @computed_field(return_type=str)
    @property
    def text(self):
        return self.as_full_text()

    def as_text(self):
        if self.is_bot:
            return f"BOT: {self.content}\n"
        else:
            return f"HUMAN: {self.content}\n"

    def as_full_text(self):
        # Assuming 'attachments' is a list of strings after processing with 'extract_attachment_text'.
        attachments_str = '\n'.join(self.attachments)
        return f"{self.content}\n\n{attachments_str}\n\n{self.timestamp} {self.jump_url}\n"

    def __str__(self):
        return self.as_full_text()

class ChatThread(DataObjectModel):
    """
    A conversation between a human and an AI. In Discord, this is a `Thread`
    """
    type: ServerDataObjectTypes = ServerDataObjectTypes.THREAD
    messages: List[DiscordContentMessage] = Field(default_factory=list)

    
    def as_path(self, title: str) -> str:
        return self.context_route.as_path(title)

    def as_text(self) -> str:
        return f"Thread: {self.name}\n" + "\n".join([message.as_text() for message in self.messages])

    def file_name(self) -> str:
        return f"{self.ai_analysis.title}-{self.id}.md"

    def as_full_text(self) -> str:
        out_string = ""
        if self.ai_analysis is not None:
            out_string += f"# {self.ai_analysis.title}\n\n> Thread: {self.name}\n"
            out_string += "AI Analysis/Summary:\n\n"+self.ai_analysis.to_string()
            out_string+= "\n______________\nFULL THREAD TEXT:\n\n"
        else:
            out_string += f"Thread: {self.name}\n"
        out_string += "\n".join([message.as_full_text() for message in self.messages])

        return out_string

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'messages'})


class ChannelData(DataObjectModel):
    type: ServerDataObjectTypes = ServerDataObjectTypes.CHANNEL
    channel_description_prompt: Optional[str] = ''
    pinned_messages: List[DiscordContentMessage] = Field(default_factory=list)
    chat_threads: Dict[str, ChatThread] = Field(default_factory=dict)
    messages: List[DiscordContentMessage] = Field(default_factory=list)

    @property
    def channel_system_prompt(self) -> str:
        return self.channel_description_prompt + "/n".join([message.content for message in self.pinned_messages])

    def as_text(self) -> str:
        return f"Channel: {self.name}\n" + "\n".join([thread.as_text() for thread in self.chat_threads.values()])

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'chat_threads'})


class CategoryData(DataObjectModel):
    """
    A Category (group of Text Channels
    """
    type: ServerDataObjectTypes = ServerDataObjectTypes.CATEGORY
    channels: Dict[str, ChannelData] = Field(default_factory=dict)
    bot_prompt_messages: List[DiscordContentMessage] = Field(default_factory=list)

    @property
    def category_system_prompt(self) -> str:
        return "/n".join([message.content for message in self.bot_prompt_messages])

    def as_text(self) -> str:
        return f"Category: {self.name}\n" + "\n".join([channel.as_text() for channel in self.channels.values()])

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'channels'})


