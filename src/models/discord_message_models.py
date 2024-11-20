from datetime import datetime
from typing import List

import aiohttp
import discord
from pydantic import BaseModel, Field, computed_field


class ContentMessage(BaseModel):
    user_id: int
    is_bot: bool
    message_id:int
    content: str = Field(default_factory=str,
                         description='The content of the message, as from `discord.message.clean_content`')
    jump_url: str = Field(default_factory=str,
                          description='The URL that links to the message in the Discord chat')
    attachments: List[str] = Field(default_factory=list,
                                   alias='Attachments',
                                   description='A list of text any (text) attachments in the message, wrapped in '
                                               '`START [filename](url) END [filename](url)`')
    timestamp: datetime = Field(default_factory=datetime.now,
                                description='The timestamp of the message in ISO 8601 format')
    reactions: List[str] = Field(default_factory=list,
                                 description='A list of reactions to the message')
    parent_message_id: int|None = Field(default=None,
                                      description='The ID of the parent message, if this message is a reply')
    embedding: List[float]|None = Field(default=None,
                                      description='The embedding vector of the message')
    @computed_field
    @property
    def is_reply(self) -> bool:
        return self.parent_message_id is not None

    @computed_field
    @property
    def id(self) -> int:
        return self.message_id


    @classmethod
    def from_discord_message(cls, discord_message: discord.Message):
        return cls(
            message_id =discord_message.id,
            user_id=discord_message.author.id,
            is_bot=discord_message.author.bot,
            content=discord_message.clean_content,
            jump_url=discord_message.jump_url,
            attachments=[attachment.url for attachment in discord_message.attachments],
            timestamp=discord_message.created_at,
            reactions=[reaction.emoji for reaction in discord_message.reactions],
            parent_message_id = discord_message.reference.message_id if discord_message.reference else None
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
                    attachment_string += await resp.text()
        attachment_string += f" END [{attachment.filename}]({attachment.url})"
        return attachment_string

    @computed_field(return_type=str)
    @property
    def text(self):
        return self.as_text()

    def as_text(self):
        if self.is_bot:
            return f"BOT: {self.content}\n"
        else:
            return f"HUMAN: {self.content}\n"


    def __str__(self):
        # Assuming 'attachments' is a list of strings after processing with 'extract_attachment_text'.
        attachments_str = '\n'.join(self.attachments)
        return f"{self.content}\n\n{attachments_str}\n\n{self.timestamp.isoformat()} {self.jump_url}\n"
