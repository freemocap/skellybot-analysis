import pickle
from pathlib import Path
from pprint import pprint
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from src.ai.text_analysis_prompt_model import TextAnalysisPromptModel
from src.scrape_server.models.discord_message_models import ContentMessage

EmbeddingVectors = Dict[str, List[float]]


class AIAnalysis(BaseModel):
    original_text: str
    summary_prompt: str
    summary_response: str
    context_text: str
    context_response: str
    tags: str
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
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embeddings: Dict[str, List[float]] = Field(default_factory=dict,
                                       description="Key: embeddings sourve, Value: embedding vector")

    def as_text(self) -> str:
        return f"Thread: {self.name}\n" + "\n".join([message.as_text() for message in self.messages])


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
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embeddings: Dict[str, List[float]] = Field(default_factory=dict,
                                       description="Key: embeddings sourve, Value: embedding vector")

    @property
    def channel_system_prompt(self) -> str:
        return self.channel_description_prompt + "/n".join([message.content for message in self.pinned_messages])

    def as_text(self) -> str:
        return f"Channel: {self.name}\n" + "\n".join([thread.as_text() for thread in self.chat_threads.values()])


class CategoryData(BaseModel):
    """
    A Category (group of Text Channels
    """
    name: str
    id: int
    channels: Dict[str, ChannelData] = Field(default_factory=dict)
    bot_prompt_messages: List[ContentMessage] = Field(default_factory=list)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embeddings: Dict[str, List[float]] = Field(default_factory=dict,
                                       description="Key: embeddings sourve, Value: embedding vector")

    @property
    def category_system_prompt(self) -> str:
        return "/n".join([message.content for message in self.bot_prompt_messages])

    def as_text(self) -> str:
        return f"Category: {self.name}\n" + "\n".join([channel.as_text() for channel in self.channels.values()])


class ServerData(BaseModel):
    name: str
    id: int
    bot_prompt_messages: List[ContentMessage] = Field(default_factory=list)
    categories: Dict[str, CategoryData] = Field(default_factory=dict)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embeddings: Dict[str, List[float]] = Field(default_factory=dict,
                                       description="Key: embeddings sourve, Value: embedding vector")

    @property
    def server_system_prompt(self) -> str:
        return "/n".join([message.content for message in self.bot_prompt_messages])

    def as_text(self) -> str:
        return f"Server: {self.name}\n" + "\n".join([category.as_text() for category in self.categories.values()])

    def get_messages(self) -> List[ContentMessage]:
        messages = []
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                for thread_key, thread_data in channel_data.chat_threads.items():
                    for message in thread_data.messages:
                        messages.append(message)
        return messages

    def get_chat_threads(self) -> List[ChatThread]:
        chat_threads = []
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                for thread_key, thread_data in channel_data.chat_threads.items():
                    chat_threads.append(thread_data)
        return chat_threads

    def get_channels(self) -> List[ChannelData]:
        channels = []
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                channels.append(channel_data)
        return channels

    def get_categories(self) -> List[CategoryData]:
        categories = []
        for category_key, category_data in self.categories.items():
            categories.append(category_data)
        return categories

    def stats(self) -> Dict[str, str]:
        stats = {}
        stats['name'] = self.name
        stats['id'] = self.id
        stats['categories'] = len(self.categories)
        stats['channels'] = sum([len(category.channels) for category in self.categories.values()])
        stats['chat_threads'] = sum([len(channel.chat_threads) for category in self.categories.values() for channel in
                                     category.channels.values()])
        stats['messages'] = sum(
            [len(thread.messages) for category in self.categories.values() for channel in category.channels.values() for
             thread in channel.chat_threads.values()])
        stats['words'] = {}
        stats['words']['total'] = sum([len(message.content.split()) for message in self.get_messages()])
        stats['words']['human'] = sum(
            [len(message.content.split()) for message in self.get_messages() if message.is_bot == False])
        stats['words']['bot'] = sum(
            [len(message.content.split()) for message in self.get_messages() if message.is_bot == True])
        return stats


if __name__ == '__main__':
    from src.utilities.get_most_recent_server_data import get_most_recent_scrape_location

    paths = get_most_recent_scrape_location()
    server_data = pickle.load(open(str(Path(paths['pickle'])), 'rb'))
    pprint(server_data.stats())
