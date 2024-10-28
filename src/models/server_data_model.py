import pickle
from typing import Dict, List

from pydantic import BaseModel, Field
from src.models.content_message_models import ContentMessage


class ChatThread(BaseModel):
    """
    A conversation between a human and an AI. In Discord, this is a `Thread`
    """
    name: str
    id: int
    # couplets: List[Couplet] = Field(default_factory=list)
    messages: List[ContentMessage] = Field(default_factory=list)


class ChannelData(BaseModel):
    """
    The Data from a Text Channel in a discord server
    """
    name: str
    id: int
    channel_description_prompt: str = ''
    pinned_messages: List[ContentMessage] = Field(default_factory=list)
    chat_threads: Dict[str, ChatThread] = Field(default_factory=dict)
    messages: List[ContentMessage] = Field(default_factory=list)


class CategoryData(BaseModel):
    """
    A Category (group of Text Channels
    """
    name: str
    id: int
    channels: Dict[str, ChannelData] = Field(default_factory=dict)
    bot_prompt_messages: List[ContentMessage] = Field(default_factory=list)


class ServerData(BaseModel):
    name: str
    id: int
    bot_prompt_messages: List[ContentMessage] = Field(default_factory=list)
    categories: Dict[str, CategoryData] = Field(default_factory=dict)


if __name__ == '__main__':
    pickle_path = r"C:\Users\jonma\Sync\skellybot-data\2024 NEU Capstone_2024-04-07_12-45-43.pkl"
    output_directory = r"C:\Users\jonma\Sync\skellybot-data"
    server_data = pickle.load(open(pickle_path, 'rb'))
    server_data.save_as_markdown_directory(output_directory)
