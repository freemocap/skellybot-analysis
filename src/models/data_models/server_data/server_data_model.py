from pprint import pprint
from typing import Dict, List, Any

import numpy as np
from pydantic import Field
from sklearn.manifold import TSNE

from src.ai.get_embeddings_for_text import get_embedding_for_text
from src.ai.openai_constants import OPENAI_CLIENT
from src.models.data_models.data_object_model import DataObjectModel
from src.models.data_models.graph_data_models import GraphData, ServerNode, \
    CategoryNode, ParentLink, ChannelNode, TagNode, TagLink, ThreadNode, UserNode
from src.models.data_models.server_data.server_context_route_model import ServerContextRoute
from src.models.data_models.server_data.server_data_object_types_enum import ServerDataObjectTypes
from src.models.data_models.server_data.server_data_stats import ServerDataStats
from src.models.data_models.server_data.server_data_sub_object_models import DiscordContentMessage, ChatThread, \
    ChannelData, CategoryData
from src.models.data_models.server_data.user_data_model import UserData
from src.models.data_models.xyz_data_model import XYZData
from src.models.text_analysis_prompt_model import TagModel
from src.utilities.load_env_variables import DISCORD_DEV_BOT_ID, DISCORD_BOT_ID

EmbeddingVectors = Dict[str, List[float]]

PROF_JON_USER_ID = 362711467104927744
EXCLUDED_USER_IDS = [DISCORD_BOT_ID, DISCORD_DEV_BOT_ID]  # , PROF_JON_USER_ID]

NODE_SIZE_EXPONENT = 2
TSNE_SEED = 42
TSNE_DIMENSIONS = 3
TSNE_PERPLEXITY = 25

MAX_MESSAGE_CHAIN_LENGTH = None
THREADS_AS_CHAINS = False


class ServerData(DataObjectModel):
    type: ServerDataObjectTypes = ServerDataObjectTypes.SERVER
    bot_prompt_messages: List[DiscordContentMessage] = Field(default_factory=list)

    categories: Dict[str, CategoryData] = Field(default_factory=dict)
    users: Dict[int, UserData] = Field(default_factory=dict)
    graph_data: GraphData | None = None

    @property
    def server_system_prompt(self) -> str:
        return "/n".join([message.content for message in self.bot_prompt_messages])

    @property
    def stats(self) -> ServerDataStats:
        return ServerDataStats(id=self.id,
                               name=self.name,
                               type=self.type,
                               categories=len(self.categories),
                               channels=sum([len(category.channels) for category in self.categories.values()]),
                               threads=sum(
                                   [len(channel.chat_threads) for category in self.categories.values() for channel in
                                    category.channels.values()]),
                               messages=sum(
                                   [len(thread.messages) for category in self.categories.values() for channel in
                                    category.channels.values() for thread in channel.chat_threads.values()]),
                               total_words=sum(
                                   [len(message.content.split()) for category in self.categories.values() for channel in
                                    category.channels.values() for thread in channel.chat_threads.values() for message
                                    in thread.messages]),
                               human_words=sum(
                                   [len(message.content.split()) for category in self.categories.values() for channel in
                                    category.channels.values() for thread in channel.chat_threads.values() for message
                                    in thread.messages if message.is_bot == False]),
                               bot_words=sum(
                                   [len(message.content.split()) for category in self.categories.values() for channel in
                                    category.channels.values() for thread in channel.chat_threads.values() for message
                                    in thread.messages if message.is_bot == True])
                               )

    def as_text(self) -> str:
        return f"Server: {self.name}\n" + "\n".join([category.as_text() for category in self.categories.values()])

    def all_tags(self) -> List[TagModel]:
        all_tags = []
        for thing in self.get_all_sub_objects():
            if hasattr(thing, "ai_analysis") and hasattr(thing.ai_analysis, "tags_list"):
                all_tags.extend(thing.tags)
        return all_tags

    def get_all_sub_objects(self) -> List[DataObjectModel]:
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

    def get_messages(self) -> List[DiscordContentMessage]:
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

    def get_users(self) -> Dict[int, UserData]:
        self.extract_user_data()
        return self.users

    def extract_user_data(self) -> Dict[int, UserData]:
        user_threads = {}
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                for thread_key, thread_data in channel_data.chat_threads.items():
                    for message in thread_data.messages:
                        if message.author_id in EXCLUDED_USER_IDS:
                            continue
                        if message.author_id not in user_threads:
                            user_threads[message.author_id] = []
                        user_threads[message.author_id].append(thread_data)

        for user_id, chats in user_threads.items():
            self.users[user_id] = UserData(id=user_id,
                                           name=f"User {user_id}",
                                           context_route=ServerContextRoute(
                                               server_name=self.name,
                                               server_id=self.id,
                                           ),
                                           threads=chats)

        return self.users

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'categories', 'users', 'graph_data'})

    async def calculate_embedding_tsne(self):

        all_server_things = self.get_all_sub_objects()
        all_server_tags = self.all_tags()
        all_things = all_server_things + all_server_tags
        for thing in all_things:
            if not hasattr(thing, 'embedding'):
                raise ValueError(f"No embedding found for {thing.__class__.__name__}: {thing.name}")

        embeddings = [await get_embedding_for_text(client=OPENAI_CLIENT,
                                                   text_to_embed=thing.as_text()) for thing in all_things]
        if not embeddings:
            raise ValueError("No embeddings found for server data")

        embeddings_array = np.array(embeddings)
        tsne = TSNE(n_components=TSNE_DIMENSIONS, perplexity=TSNE_PERPLEXITY, random_state=TSNE_SEED)
        tsne_results = tsne.fit_transform(embeddings_array)

        for tsne_xyz, thing in zip(tsne_results, all_things):
            thing.tsne_xyz = XYZData(x=tsne_xyz[0], y=tsne_xyz[1], z=tsne_xyz[2])

    async def calculate_graph_data(self):
        await self.calculate_embedding_tsne()
        nodes = []
        links = []

        server_node_id = f"server-{self.id}"
        server_node_name = self.name

        group_number = -1

        def group_number_incrementer():
            nonlocal group_number
            group_number += 1
            return group_number

        server_node = ServerNode(id=server_node_id,
                                 name=server_node_name,
                                 group=group_number_incrementer(),
                                 tsne_xyz=self.tsne_xyz,
                                 ai_analysis=self.ai_analysis.to_string(),
                                 tags=self.ai_analysis.tags_list, )
        nodes.append(server_node)

        tag_nodes = [TagNode(id=f"tag-{tag}",
                             name=tag,
                             group=group_number_incrementer(),
                             tsne_xyz=self.tsne_xyz,
                             ) for tag in self.all_tags()]
        nodes.extend(tag_nodes)

        for user in self.get_users().values():
            user_node = UserNode(id=f"user-{user.id}",
                                 name=f"User {user.id}",
                                 group=group_number_incrementer(),
                                 tsne_xyz=user.tsne_xyz,
                                 ai_analysis=user.ai_analysis.to_string(),
                                 tags=user.ai_analysis.tags_list,
                                 )
            nodes.append(user_node)

            for tag_node in tag_nodes:
                if tag_node.name in user.ai_analysis.tags_list:
                    links.append(TagLink(source=user_node.id,
                                         target=tag_node.id,
                                         group=group_number,
                                         ))

        for category_number, category in enumerate(self.categories.values()):
            category_node_id = f"category-{category.id}"
            category_name = category.name
            category_node = CategoryNode(id=category_node_id,
                                         name=category_name,
                                         group=group_number_incrementer(),
                                         tsne_xyz=category.tsne_xyz,
                                         ai_analysis=category.ai_analysis.to_string(),
                                         tags=category.ai_analysis.tags_list,
                                         )
            nodes.append(category_node)
            server_node.childLinks.append(category_node_id)
            links.append(ParentLink(source=server_node_id,
                                    target=category_node_id,
                                    ))

            for tag in category.ai_analysis.tags_list:
                tag_node = next((tag_node for tag_node in tag_nodes if tag_node.name == tag), None)
                if tag_node:
                    links.append(TagLink(source=category_node_id,
                                         target=tag_node.id,
                                         group=group_number,
                                         ))
                    tag_node.childLinks.append(category_node_id)

            for channel_number, channel in enumerate(category.channels.values()):
                if channel.name == "bot-playground":
                    continue
                channel_node_id = f"channel-{channel.id}"
                channel_name = channel.name
                channel_node = ChannelNode(id=channel_node_id,
                                           name=channel_name,
                                           group=group_number_incrementer(),
                                           tsne_xyz=channel.tsne_xyz,
                                           ai_analysis=channel.ai_analysis.to_string(),
                                           tags=channel.ai_analysis.tags_list,
                                           )
                nodes.append(channel_node)
                links.append(ParentLink(source=category_node_id,
                                        target=channel_node_id,
                                        ))
                category_node.childLinks.append(channel_node_id)
                for tag in channel.ai_analysis.tags_list:
                    tag_node = next((tag_node for tag_node in tag_nodes if tag_node.name == tag), None)
                    if tag_node:
                        links.append(TagLink(source=channel_node_id,
                                             target=tag_node.id,
                                             group=group_number,
                                             ))

                for thread_number, thread in enumerate(channel.chat_threads.values()):
                    thread_node_id = f"thread-{thread.id}"
                    thread_name = thread.ai_analysis.title
                    thread_node = ThreadNode(id=thread_node_id,
                                             name=thread_name,
                                             group=group_number_incrementer(),
                                             tsne_xyz=thread.tsne_xyz,
                                             ai_analysis=thread.ai_analysis.to_string(),
                                             tags=thread.ai_analysis.tags_list,
                                             )
                    nodes.append(thread_node)
                    links.append(ParentLink(source=channel_node_id,
                                            target=thread_node_id,
                                            group=channel_number,
                                            ))
                    channel_node.childLinks.append(thread_node_id)
                    for tag in thread.ai_analysis.tags_list:
                        tag_node = next((tag_node for tag_node in tag_nodes if tag_node.name == tag), None)
                        if tag_node:
                            links.append(TagLink(source=thread_node_id,
                                                 target=tag_node.id,
                                                 group=group_number,
                                                 ))

        self.graph_data = GraphData(nodes=nodes, links=links)
        return self.graph_data

    def calculate_tsne_embedding(self):
        embeddings = []
        for thing in self.self.get_all_sub_objects():
            if hasattr(thing, 'embedding') and thing.embedding:
                embeddings.append(thing.embedding)

        if not embeddings:
            return None

        embeddings_array = np.array(embeddings)
        tsne = TSNE(n_components=TSNE_DIMENSIONS, perplexity=TSNE_PERPLEXITY, random_state=TSNE_SEED)
        tsne_results = tsne.fit_transform(embeddings_array)

        data_thing_tsne_results = tsne_results[:len(self.get_all_sub_objects())]
        for tsne_xyz, thing in zip(data_thing_tsne_results, self.get_all_sub_objects()):
            thing.tsne_norm_magnitude = np.linalg.norm(tsne_xyz)
            thing.tsne_xyz_normalized = tsne_xyz / thing.tsne_norm_magnitude


if __name__ == '__main__':
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data, _ = get_server_data()
    server_data.extract_user_data()
    pprint(server_data.stats)
    # pprint(server_data.get_graph_data())