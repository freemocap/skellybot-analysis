from pydantic import BaseModel

import discord
from sqlmodel import SQLModel, Field

class ServerContextRoute(BaseModel):
    """
    A route to a specific context in the server data
    """
    server_name: str
    server_id: int

    category_name: str | None = None
    category_id: int | None = None

    channel_name: str | None = None
    channel_id: int | None = None

    thread_id: int | None = None
    thread_name: str | None = None

    message_id: int | None = None

    def as_path(self, title: str):

        path = f"{self.server_name}"
        if self.category_name:
            path += f"/{self.category_name}"
        if self.channel_name:
            path += f"/{self.channel_name}"
        if self.thread_name:
            path += f"/{title}-{self.thread_id}"
        return path

    @classmethod
    def from_discord_message(cls, message: discord.Message) -> "ServerContextRoute":
        return cls(
            server_name=message.guild.name,
            server_id=message.guild.id,
            category_name=message.channel.category.name if message.channel.category else None,
            category_id=message.channel.category.id if message.channel.category else None,
            channel_name=message.channel.name,
            channel_id=message.channel.id,
            thread_name=message.thread.name if message.thread else None,
            thread_id=message.thread.id if message.thread else None,
            message_id=message.id
        )
