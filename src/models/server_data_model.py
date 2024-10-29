import pickle
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from src.models.content_message_models import ContentMessage

EmbeddingVectors = Dict[str, List[float]]

class AIAnalysis(BaseModel):
    original_text: str
    summary_prompt: str
    summary_response: str
    context_text: str
    context_response: str
    tags:str
    fluff_text: bool
    embeddings: EmbeddingVectors

class ChatThread(BaseModel):
    """
    A conversation between a human and an AI. In Discord, this is a `Thread`
    """
    name: str
    id: int
    # couplets: List[Couplet] = Field(default_factory=list)
    messages: List[ContentMessage] = Field(default_factory=list)
    ai_analysis: AIAnalysis | None = None

class ChannelData(BaseModel):
    """
    The Data from a Text Channel in a discord server
    """
    name: str
    id: int
    channel_description_prompt: Optional[str] = ''
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

    def get_messages(self):
        messages = []
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                for thread_key, thread_data in channel_data.chat_threads.items():
                    for message in thread_data.messages:
                        messages.append(message)
        return messages

    def get_chat_threads(self):
        chat_threads = []
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                for thread_key, thread_data in channel_data.chat_threads.items():
                    chat_threads.append(thread_data)
        return chat_threads

    def get_channels(self):
        channels = []
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                channels.append(channel_data)
        return channels

    def get_categories(self):
        categories = []
        for category_key, category_data in self.categories.items():
            categories.append(category_data)
        return categories


if __name__ == '__main__':
    pickle_path = r"C:\Users\jonma\Sync\skellybot-data\2024 NEU Capstone_2024-04-07_12-45-43.pkl"
    output_directory = r"C:\Users\jonma\Sync\skellybot-data"
    server_data = pickle.load(open(pickle_path, 'rb'))
    server_data.save_as_markdown_directory(output_directory)
