from datetime import datetime

import aiohttp
import discord
from pydantic import BaseModel, Field


class ParquetDiscordThread(BaseModel):
    thread_id: int
    name: str
    server_id: int
    server_name: str
    category_id: int | float | None = None
    category_name: str | None = None
    channel_id: int
    channel_name: str

    owner_id: int

    jump_url: str

    created_at: datetime


class ParquetDiscordUser(BaseModel):
    user_id: int
    server_id: int
    is_bot: bool
    joined_at: datetime


class ParquetContextPrompt(BaseModel):
    context_id: int
    server_id: int
    server_name: str
    prompt_text: str
    category_id: int | None
    category_name: str | None
    channel_id: int | None
    channel_name: str | None


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


class ParquetDiscordMessage(BaseModel):
    message_id: int
    content: str
    author_id: int
    jump_url: str

    parent_message_id: int | float| None = None

    server_id: int
    server_name: str
    category_id: int | float | None = None
    category_name: str | None = None
    channel_id: int
    channel_name: str
    thread_id: int
    thread_name: str

    timestamp: datetime
    attachments: list[str] = Field(default_factory=list)
    reactions: list[str] = Field(default_factory=list)
