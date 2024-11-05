from pprint import pprint
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from src.ai.text_analysis_prompt_model import TextAnalysisPromptModel
from src.scrape_server.models.discord_message_models import ContentMessage
from src.utilities.load_env_variables import DISCORD_DEV_BOT_ID, DISCORD_BOT_ID

EmbeddingVectors = Dict[str, List[float]]

EXCLUDED_USER_IDS = [DISCORD_BOT_ID, DISCORD_DEV_BOT_ID]


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
    server_name: str
    server_id: int
    category_name: str | None = None
    category_id: int | None = None
    channel_name: str
    channel_id: int
    messages: List[ContentMessage] = Field(default_factory=list)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embedding: List[float] = Field(default_factory=list,
                                   description="The embedding vector for the entire text")

    def as_text(self) -> str:
        return f"Thread: {self.name}\n" + "\n".join([message.as_text() for message in self.messages])

    def as_full_text(self) -> str:
        out_string = f"Thread: {self.name}\n"
        if self.ai_analysis is not None:
            out_string += self.ai_analysis.to_string() + "\n______________\n"

        out_string += "\n".join([message.as_text() for message in self.messages])

        return out_string


class ChannelData(BaseModel):
    """
    The Data from a Text Channel in a discord server
    """
    name: str
    id: int
    server_name: str
    server_id: int
    category_name: str | None = None
    category_id: int | None = None
    channel_description_prompt: Optional[str] = ''
    pinned_messages: List[ContentMessage] = Field(default_factory=list)
    chat_threads: Dict[str, ChatThread] = Field(default_factory=dict)
    messages: List[ContentMessage] = Field(default_factory=list)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embedding: List[float] = Field(default_factory=list,
                                   description="The embedding vector for the entire text")

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
    server_name: str
    server_id: int
    channels: Dict[str, ChannelData] = Field(default_factory=dict)
    bot_prompt_messages: List[ContentMessage] = Field(default_factory=list)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embedding: List[float] = Field(default_factory=list,
                                   description="The embedding vector for the entire text")

    @property
    def category_system_prompt(self) -> str:
        return "/n".join([message.content for message in self.bot_prompt_messages])

    def as_text(self) -> str:
        return f"Category: {self.name}\n" + "\n".join([channel.as_text() for channel in self.channels.values()])


class UserData(BaseModel):
    user_id: int
    name: str | None = None
    threads: List[ChatThread] = Field(default_factory=list)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embedding: List[float] = Field(default_factory=list,
                                   description="The embedding vector for the entire text")

    def as_text(self) -> str:
        return f"User: {self.user_id}\n" + "\n".join([thread.as_text() for thread in self.threads])

    def as_full_text(self) -> str:
        return f"User: {self.user_id}\n" + self.ai_analysis.to_string() + "\n______________\n" + "\n".join(
            [thread.as_text() for thread in self.threads])

    def stats(self) -> Dict[str, str]:
        stats = {}
        stats['user_id'] = str(self.user_id)
        stats['threads'] = len(self.threads)
        stats['messages'] = sum([len(thread.messages) for thread in self.threads])
        stats['words'] = {}
        stats['words']['total'] = sum(
            [len(message.content.split()) for thread in self.threads for message in thread.messages])
        stats['words']['human'] = sum(
            [len(message.content.split()) for thread in self.threads for message in thread.messages if
             message.is_bot == False])
        stats['words']['bot'] = sum(
            [len(message.content.split()) for thread in self.threads for message in thread.messages if
             message.is_bot == True])
        return stats


class ServerData(BaseModel):
    name: str
    id: int
    bot_prompt_messages: List[ContentMessage] = Field(default_factory=list)
    categories: Dict[str, CategoryData] = Field(default_factory=dict)
    users: Dict[int, UserData] = Field(default_factory=dict)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embedding: List[float] = Field(default_factory=list,
                                   description="The embedding vector for the entire text")

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

    def get_chats_by_user(self) -> Dict[int, UserData]:
        user_chats = {}
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                for thread_key, thread_data in channel_data.chat_threads.items():
                    for message in thread_data.messages:
                        if message.user_id not in user_chats and not message.is_bot:
                            user_chats[message.user_id] = []
                            user_chats[message.user_id].append(thread_data)

        for user_id, chats in user_chats.items():
            self.users[user_id] = UserData(user_id=user_id,
                                           threads=chats)

        return self.users

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
        stats['users']['total'] = len(self.users)
        stats['users']['data'] = {user_id: user.stats() for user_id, user in self.users.items()}
        return stats


if __name__ == '__main__':
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data, _ = get_server_data()
    pprint(server_data.stats())
