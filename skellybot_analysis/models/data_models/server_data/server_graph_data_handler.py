from collections import deque

import numpy as np
from sklearn.manifold import TSNE

from src.models.data_models.graph_data_models import GraphNode, NodeTypes, GraphData, GraphLink

from pydantic import BaseModel

from src.models.data_models.server_data.server_data_model import ServerData

NODE_SIZE_EXPONENT = 2
TSNE_SEED = 42
TSNE_DIMENSIONS = 3
TSNE_PERPLEXITY = 25

MAX_MESSAGE_CHAIN_LENGTH = None
THREADS_AS_CHAINS = False

# class ServerGraphDataCalculator(BaseModel):
#     graph_data: GraphData
#
#     @classmethod
#     def calculate_graph_connections(cls, server_data: ServerData):
#         nodes = []
#         links = []
#
#         server_node_id = f"server-{server_data.id}"
#         server_node_name = server_data.name
#         nodes.append(GraphNode(id=server_node_id,
#                                name=server_node_name,
#                                group=0,
#                                type=NodeTypes.SERVER.name.lower(),
#                                level=NodeTypes.SERVER.value,
#                                root=True,
#                                relative_size=NodeTypes.SERVER.value ** NODE_SIZE_EXPONENT,
#                                tsne_xyz=server_data.tsne_xyz_normalized,
#                                tsne_norm_magnitude=server_data.tsne_norm_magnitude,
#                                ai_analysis=server_data.ai_analysis.to_string()
#                                ))
#
#         for category_number, category in enumerate(server_data.categories.values()):
#             category_node_id = f"category-{category.id}"
#             category_name = category.name
#
#             nodes.append(GraphNode(id=category_node_id,
#                                    name=category_name,
#                                    group=category_number,
#                                    type=NodeTypes.CATEGORY.name.lower(),
#                                    level=NodeTypes.CATEGORY.value,
#                                    relative_size=NodeTypes.CATEGORY.value ** NODE_SIZE_EXPONENT,
#                                    tsne_xyz=category.tsne_xyz_normalized,
#                                    tsne_norm_magnitude=category.tsne_norm_magnitude,
#                                    ai_analysis=category.ai_analysis.to_string(),
#                                    ))
#             links.append(GraphLink(source=server_node_id,
#                                    target=category_node_id,
#                                    type='parent',
#                                    group=category_number,
#                                    ))
#
#             for channel_number, channel in enumerate(category.channels.values()):
#                 if channel.name == "bot-playground":
#                     continue
#                 channel_node_id = f"channel-{channel.id}"
#                 channel_name = channel.name
#                 nodes.append(GraphNode(id=channel_node_id,
#                                        name=channel_name,
#                                        group=category_number,
#                                        type=NodeTypes.CHANNEL.name.lower(),
#                                        level=NodeTypes.CHANNEL.value,
#                                        relative_size=NodeTypes.CHANNEL.value ** NODE_SIZE_EXPONENT,
#                                        tsne_xyz=server_data.tsne_xyz_normalized,
#                                        tsne_norm_magnitude=server_data.tsne_norm_magnitude,
#                                        ai_analysis=channel.ai_analysis.to_string(),
#                                        ))
#                 links.append(GraphLink(source=category_node_id,
#                                        target=channel_node_id,
#                                        type="parent",
#                                        group=category_number,
#                                        ))
#
#                 for thread_number, thread in enumerate(channel.chat_threads.values()):
#                     thread_node_id = f"thread-{thread.id}"
#                     thread_name = thread.ai_analysis.title
#                     nodes.append(GraphNode(id=thread_node_id,
#                                            name=thread_name,
#                                            group=channel_number,
#                                            type=NodeTypes.THREAD.name.lower(),
#                                            level=NodeTypes.THREAD.value,
#                                            relative_size=NodeTypes.THREAD.value ** NODE_SIZE_EXPONENT,
#                                            tsne_xyz=thread.tsne_xyz_normalized,
#                                            tsne_norm_magnitude=thread.tsne_norm_magnitude,
#                                            ai_analysis=thread.ai_analysis.to_string(),
#                                            ))
#                     links.append(GraphLink(source=channel_node_id,
#                                            target=thread_node_id,
#                                            type='parent',
#                                            group=channel_number,
#                                            ))
#
#         self.graph_data = GraphData(nodes=nodes, links=links)
#
#     @classmethod
#     def calculate_tsne_embedding(cls, server_data: ServerData):
#         embeddings = []
#         for thing in self.server_data.get_all_things():
#             if hasattr(thing, 'embedding') and thing.embedding:
#                 embeddings.append(thing.embedding)
#
#         if not embeddings:
#             return None
#
#         embeddings_array = np.array(embeddings)
#         tsne = TSNE(n_components=TSNE_DIMENSIONS, perplexity=TSNE_PERPLEXITY, random_state=TSNE_SEED)
#         tsne_results = tsne.fit_transform(embeddings_array)
#
#
#         data_thing_tsne_results = tsne_results[:len(server_data.get_all_things())]
#         for tsne_xyz, thing in zip(data_thing_tsne_results, server_data.get_all_things()):
#             thing.tsne_norm_magnitude = np.linalg.norm(tsne_xyz)
#             thing.tsne_xyz_normalized = tsne_xyz / thing.tsne_norm_magnitude
