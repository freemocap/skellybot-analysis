import asyncio
from datetime import datetime
from pprint import pprint
from typing import Dict, List

from pydantic import Field

from skellybot_analysis.models.data_models.data_object_model import DataObjectModel
from skellybot_analysis.models.data_models.graph_data_models import GraphData, ServerNode, \
    CategoryNode, ParentLink, ChannelNode, ThreadNode
from skellybot_analysis.models.data_models.server_data.server_context_route_model import ServerContextRoute
from skellybot_analysis.models.data_models.server_data.server_data_object_types_enum import ServerDataObjectTypes
from skellybot_analysis.models.data_models.server_data.server_data_stats import ServerDataStats
from skellybot_analysis.models.data_models.server_data.server_data_sub_object_models import DiscordContentMessage, \
    ChatThread, \
    ChannelData, CategoryData
from skellybot_analysis.models.data_models.user_data_model import UserData, UserDataManager
from skellybot_analysis.utilities.load_env_variables import DISCORD_DEV_BOT_ID, DISCORD_BOT_ID

import logging
logger = logging.getLogger(__name__)

PROF_JON_USER_ID = 362711467104927744
EXCLUDED_USER_IDS = [DISCORD_BOT_ID, DISCORD_DEV_BOT_ID]  # , PROF_JON_USER_ID]


class ServerData(DataObjectModel):
    type: ServerDataObjectTypes = ServerDataObjectTypes.SERVER
    bot_prompt_messages: List[DiscordContentMessage] = Field(default_factory=list)

    categories: Dict[str, CategoryData] = Field(default_factory=dict)

    graph_data: GraphData|None=None

    @property
    def server_system_prompt(self) -> str:
        return "/n".join([message.content for message in self.bot_prompt_messages])

    @property
    def latest_message_timestamp(self) -> str:
        messages = self.get_messages()
        message_timestamps = [datetime.fromisoformat(message.timestamp) for message in messages]
        return max(message_timestamps).isoformat()

    @property
    def stats(self) -> ServerDataStats:
        return ServerDataStats(id=self.id,
                               name=self.name,
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
                                  in thread.messages if message.is_bot == True]),
                               users = self.extract_user_data(assignments_channel_only=False).stats,
                               # tags = self.extract_tag_data().stats,
                               )

    def as_text(self) -> str:
        return f"Server: {self.name}\n" + "\n".join([category.as_text() for category in self.categories.values()])



    def get_all_sub_objects(self,
                            include_messages: bool = False) -> List[DataObjectModel]:
        things = [self]
        things.extend(self.get_categories())
        things.extend(self.get_channels())
        things.extend(self.get_chat_threads())
        if include_messages:
            things.extend(self.get_messages())
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

    def get_channels(self, exclude_bot_playground: bool = True) -> List[ChannelData]:
        channels = []
        for category_key, category_data in self.categories.items():
            for channel_key, channel_data in category_data.channels.items():
                if exclude_bot_playground and channel_data.name == "bot-playground":
                    continue
                channels.append(channel_data)
        return channels

    def get_categories(self) -> List[CategoryData]:
        categories = []
        for category_key, category_data in self.categories.items():
            categories.append(category_data)
        return categories

    def extract_user_data(self, assignments_channel_only:bool) -> UserDataManager:
        user_threads = {}

        for thread in self.get_chat_threads():
            if assignments_channel_only:
                if "assignments" not in thread.context_route.category_name.lower():
                    continue
            for message in thread.messages:
                if message.author_id in EXCLUDED_USER_IDS:
                    continue
                if message.is_bot:
                    continue
                if message.author_id not in user_threads:
                    user_threads[message.author_id] = []
                if thread not in user_threads[message.author_id]:
                    user_threads[message.author_id].append(thread)

        user_data_manager = UserDataManager()
        for user_id, chats in user_threads.items():
            user_data_manager.add_user(UserData(id=user_id,
                                      name=f"User {user_id}",
                                      context_route=ServerContextRoute(
                                          server_name=self.name,
                                          server_id=self.id,
                                      ),
                                      threads=chats))

        return user_data_manager


    def calculate_graph_data(self):
        try:
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
                                     group=group_number_incrementer() )
            nodes.append(server_node)

            for category_number, category in enumerate(self.categories.values()):
                category_node_id = f"category-{category.id}"
                category_name = category.name
                category_node = CategoryNode(id=category_node_id,
                                             name=category_name,
                                             group=group_number_incrementer(),
                                             )
                nodes.append(category_node)
                server_node.childLinks.append(category_node_id)
                links.append(ParentLink(source=server_node_id,
                                        target=category_node_id,
                                        ))

                for channel_number, channel in enumerate(category.channels.values()):
                    if channel.name == "bot-playground":
                        continue
                    channel_node_id = f"channel-{channel.id}"
                    channel_name = channel.name
                    channel_node = ChannelNode(id=channel_node_id,
                                               name=channel_name,
                                               group=group_number_incrementer(),
                                               )
                    nodes.append(channel_node)
                    links.append(ParentLink(source=category_node_id,
                                            target=channel_node_id,
                                            ))
                    category_node.childLinks.append(channel_node_id)

                    for thread_number, thread in enumerate(channel.chat_threads.values()):
                        thread_node_id = f"thread-{thread.id}"
                        thread_name = thread.name
                        thread_node = ThreadNode(id=thread_node_id,
                                                 name=thread_name,
                                                 group=group_number_incrementer(),
                                                 )
                        nodes.append(thread_node)
                        links.append(ParentLink(source=channel_node_id,
                                                target=thread_node_id,
                                                group=channel_number,
                                                ))
                        channel_node.childLinks.append(thread_node_id)
        except Exception as e:
            logger.exception("Error calculating Server Graph data")
            raise
        self.graph_data =  GraphData(nodes=nodes, links=links)


if __name__ == '__main__':
    from skellybot_analysis.utilities.get_most_recent_server_data import get_server_data

    server_data, _ = get_server_data()
    server_data.calculate_graph_data()
    pprint(server_data.stats)
    # pprint(server_data.get_graph_data())
