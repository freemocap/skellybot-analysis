from dataclasses import dataclass
from pprint import pprint
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, computed_field
from src.models.text_analysis_prompt_model import TextAnalysisPromptModel
from src.models.discord_message_models import ContentMessage

from src.utilities.load_env_variables import DISCORD_DEV_BOT_ID, DISCORD_BOT_ID

EmbeddingVectors = Dict[str, List[float]]

PROF_JON_USER_ID = 362711467104927744
EXCLUDED_USER_IDS = [DISCORD_BOT_ID, DISCORD_DEV_BOT_ID, PROF_JON_USER_ID]


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

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'messages'})


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

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'chat_threads'})


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

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'channels'})


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

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'threads'})

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



class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphLink(BaseModel):
    source: str
    target: str
    strength: float = 1.0
    type: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_simple_dict(self) -> Dict[str, Any]:
        return {'nodes': [{"id": node.id, "name": node.name} for node in self.nodes],
                'links': [{"source": link.source, "target": link.target} for link in self.links]}



class ServerData(BaseModel):
    name: str
    id: int
    bot_prompt_messages: List[ContentMessage] = Field(default_factory=list)
    categories: Dict[str, CategoryData] = Field(default_factory=dict)
    users: Dict[int, UserData] = Field(default_factory=dict)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    graph_data: Optional[GraphData] = None
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

    def extract_user_data(self) -> Dict[int, UserData]:
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

    def get_graph_data(self) -> GraphData:
        self.calculate_graph_connections()
        return self.graph_data


    @property
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
        stats['users'] = {}
        stats['users']['total'] = len(self.users)
        stats['users']['data'] = {user_id: user.stats() for user_id, user in self.users.items()}
        return stats

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'categories', 'users', 'graph_data'})

    def calculate_graph_connections(self):
        nodes = []
        links = []
        nodes.append(GraphNode(id=f"server-{self.id}",
                               name=self.name,
                               type="server",
                               metadata=self.model_dump_no_children()))

        for category in self.categories.values():
            nodes.append(GraphNode(id=f"category-{category.id}",
                                   name=category.name,
                                   type="category",
                                   ))
            links.append(GraphLink(source=f"server-{self.id}",
                                   target=f"category-{category.id}",
                                   type='parent',
                                   ))

            for channel in category.channels.values():
                nodes.append(GraphNode(id=f"channel-{channel.id}",
                                       name=channel.name,
                                       type="channel",
                                       ))
                links.append(GraphLink(source=f"category-{category.id}",
                                       target=f"channel-{channel.id}",
                                       type='parent',
                                       ))

                for thread in channel.chat_threads.values():
                    nodes.append(GraphNode(id=f"thread-{thread.id}",
                                           name=thread.name,
                                           type="thread",
                                           ))
                    links.append(GraphLink(source=f"channel-{channel.id}",
                                           target=f"thread-{thread.id}",
                                           type='parent',
                                           ))

                    for message_number, message in enumerate(thread.messages):

                        nodes.append(GraphNode(id=f"message-{message.id}-{message_number}",
                                               name=f"{message.content[:20]}...{message.content[-20:]}",
                                               type="message",
                                               ))
                        links.append(GraphLink(source=f"thread-{thread.id}",
                                               target=f"message-{message.id}-{message_number}",
                                               type='parent',
                                               ))
                        #
                        # if message_number > 3:
                        #     break
                        # if message_number == 0:
                        #     links.append(GraphLink(source=f"thread-{thread.id}",
                        #                            target=f"message-{message.id}-{message_number}",
                        #                            type='parent',
                        #                            ))
                        # else:
                        #     links.append(GraphLink(source=f"message-{thread.messages[message_number - 1].id}-{message_number - 1}",
                        #                            target=f"message-{message.id}-{message_number}",
                        #                            type='next',
                        #                            ))

        self.graph_data = GraphData(nodes=nodes, links=links )

if __name__ == '__main__':
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data, _ = get_server_data()
    server_data.extract_user_data()
    pprint(server_data.stats)
    # pprint(server_data.get_graph_data())