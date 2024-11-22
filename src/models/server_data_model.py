from pprint import pprint
from typing import Dict, List, Optional, Any

import numpy as np
from pydantic import BaseModel, Field
from sklearn.manifold import TSNE

from src.models.discord_message_models import ContentMessage
from src.models.graph_data_models import GraphNode, GraphLink, GraphData, NodeTypes
from src.models.text_analysis_prompt_model import TextAnalysisPromptModel
from src.utilities.load_env_variables import DISCORD_DEV_BOT_ID, DISCORD_BOT_ID

EmbeddingVectors = Dict[str, List[float]]

PROF_JON_USER_ID = 362711467104927744
EXCLUDED_USER_IDS = [DISCORD_BOT_ID, DISCORD_DEV_BOT_ID, PROF_JON_USER_ID]

NODE_SIZE_EXPONENT = 2
TSNE_SEED = 42
TSNE_DIMENSIONS = 3
TSNE_PERPLEXITY = 25

MAX_MESSAGE_CHAIN_LENGTH = None


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
    tsne_xyz_normalized: List[float] | None = None
    tsne_norm_magnitude: float | None = None

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
    tsne_xyz_normalized: List[float] | None = None
    tsne_norm_magnitude: float | None = None

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
    tsne_xyz_normalized: List[float] | None = None
    tsne_norm_magnitude: float | None = None

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
    tsne_xyz_normalized: List[float] | None = None
    tsne_norm_magnitude: float | None = None

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
    tsne_xyz_normalized: List[float] | None = None
    tsne_norm_magnitude: float | None = None

    @property
    def server_system_prompt(self) -> str:
        return "/n".join([message.content for message in self.bot_prompt_messages])

    def as_text(self) -> str:
        return f"Server: {self.name}\n" + "\n".join([category.as_text() for category in self.categories.values()])

    def get_all_things(self):
        things = [self]
        for category_key, category_data in self.categories.items():
            things.append(category_data)
            for channel_key, channel_data in category_data.channels.items():
                things.append(channel_data)
                for thread_key, thread_data in channel_data.chat_threads.items():
                    things.append(thread_data)
                    for message in thread_data.messages:
                        things.append(message)
        return things

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
        self.calculate_tsne_embedding()
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
        server_node_id = f"server-{self.id}"
        server_node_name = self.name
        nodes.append(GraphNode(id=server_node_id,
                               name=server_node_name,
                               group=0,

                               type=NodeTypes.SERVER.name.lower(),
                               level=NodeTypes.SERVER.value,
                               root=True,
                               relative_size=NodeTypes.SERVER.value ** NODE_SIZE_EXPONENT,

                               tsne_xyz=self.tsne_xyz_normalized,
                               tsne_norm_magnitude=self.tsne_norm_magnitude,
                               ))

        for category_number, category in enumerate(self.categories.values()):
            category_node_id = f"category-{category.id}"
            category_name = category.name

            nodes.append(GraphNode(id=category_node_id,
                                   name=category_name,
                                   group=category_number,

                                   type=NodeTypes.CATEGORY.name.lower(),
                                   level=NodeTypes.CATEGORY.value,
                                   relative_size=NodeTypes.CATEGORY.value ** NODE_SIZE_EXPONENT,
                                   tsne_xyz=category.tsne_xyz_normalized,
                                   tsne_norm_magnitude=category.tsne_norm_magnitude,
                                   ))
            links.append(GraphLink(source=server_node_id,
                                   target=category_node_id,
                                   type='parent',
                                   group=category_number,
                                   ))

            for channel_number, channel in enumerate(category.channels.values()):
                channel_node_id = f"channel-{channel.id}"
                channel_name = channel.name

                nodes.append(GraphNode(id=channel_node_id,
                                       name=channel_name,
                                       group=category_number,

                                       type=NodeTypes.CHANNEL.name.lower(),
                                       level=NodeTypes.CHANNEL.value,
                                       relative_size=NodeTypes.CHANNEL.value ** NODE_SIZE_EXPONENT,
                                       tsne_xyz=self.tsne_xyz_normalized,
                                       tsne_norm_magnitude=self.tsne_norm_magnitude,
                                       # metadata=channel.model_dump_no_children(),
                                       ))
                links.append(GraphLink(source=category_node_id,
                                       target=channel_node_id,
                                       type="parent",
                                       group=category_number,
                                       ))

            for thread_number, thread in enumerate(channel.chat_threads.values()):
                thread_node_id = f"thread-{thread.id}"
                thread_name = thread.name
                nodes.append(GraphNode(id=thread_node_id,
                                       name=thread_name,
                                       group=channel_number,

                                       type=NodeTypes.THREAD.name.lower(),
                                       level=NodeTypes.THREAD.value,
                                       relative_size=NodeTypes.THREAD.value ** NODE_SIZE_EXPONENT,
                                       # metadata=thread.model_dump_no_children(),
                                       ))
                links.append(GraphLink(source=channel_node_id,
                                       target=thread_node_id,
                                       type='parent',
                                       group=channel_number,
                                       ))

                message_parent_id = thread_node_id
                for message_number, message in enumerate(thread.messages):
                    if MAX_MESSAGE_CHAIN_LENGTH and message_number > MAX_MESSAGE_CHAIN_LENGTH:
                        break
                    message_node_id = f"message-{message.id}-{message_number}"

                    if len(message.content) < 40:
                        message_name = message.content
                    else:
                        message_name = f"{message.content[:20]}...{message.content[-20:]}"

                    nodes.append(GraphNode(id=message_node_id,
                                           name=message_name,
                                           group=category_number,
                                           type=NodeTypes.MESSAGE.name.lower(),
                                           level=NodeTypes.MESSAGE.value,
                                           relative_size=NodeTypes.MESSAGE.value ** NODE_SIZE_EXPONENT,
                                           tsne_xyz=message.tsne_xyz_normalized,
                                           tsne_norm_magnitude=message.tsne_norm_magnitude,
                                           ))
                    links.append(GraphLink(source=message_parent_id,
                                           target=message_node_id,
                                           type='parent',
                                           group=category_number,
                                           ))
                    message_parent_id = message_node_id
        self.graph_data = GraphData(nodes=nodes, links=links)

    def calculate_tsne_embedding(self):
        # Collect all embeddings from categories
        embeddings = []
        for thing in self.get_all_things():
            if hasattr(thing, 'embedding') and thing.embedding:
                embeddings.append(thing.embedding)

        if not embeddings:
            return None

        # Convert to numpy array
        embeddings_array = np.array(embeddings)

        # Calculate TSNE embedding
        tsne = TSNE(n_components=TSNE_DIMENSIONS,
                    perplexity=TSNE_PERPLEXITY,
                    random_state=TSNE_SEED)
        tsne_results = tsne.fit_transform(embeddings_array)

        # Normalize the TSNE results

        for tsne_xyz, thing in zip(tsne_results, self.get_all_things()):
            thing.tsne_norm_magnitude = np.linalg.norm(tsne_xyz)
            thing.tsne_xyz_normalized = tsne_xyz / thing.tsne_norm_magnitude


if __name__ == '__main__':
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data, _ = get_server_data()
    server_data.extract_user_data()
    pprint(server_data.stats)
    # pprint(server_data.get_graph_data())
