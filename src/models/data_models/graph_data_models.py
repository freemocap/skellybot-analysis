from enum import Enum
from pprint import pprint
from typing import List

from pydantic import BaseModel


class NodeTypes(Enum):
    DEFAULT: int = 0
    MESSAGE: int = 1
    THREAD: int = 2
    CHANNEL: int = 3
    CATEGORY: int = 4
    SERVER: int = 5
    TAG: int = -1
    USER: int = -2


class LinkTypes(Enum):
    DEFAULT: int = 0
    PARENT: int = 1
    TAG: int = 2
    THREAD: int = 3
    SEMANTIC: int = 4
    USER: int = 5


class GraphNode(BaseModel):
    id: str
    name: str

    childLinks: List[str] = []  # List of link IDs
    collapsed: bool = False

    # links: List[str] = [] # List of link IDs

    node_type: NodeTypes = NodeTypes.DEFAULT.name.lower()
    val: int = NodeTypes.DEFAULT.value
    group: int = 0
    relative_size: float = 1.0
    ai_analysis: str | None = None
    tsne_xyz: List[float] | None = None
    tags: List[str] = []
    # color: str = "#F8F8FF" # Ghost White
    # metadata: Dict[str, Any] = Field(default_factory=dict)


class ServerNode(GraphNode):
    node_type: NodeTypes = NodeTypes.SERVER.name.lower()
    val: int = NodeTypes.SERVER.value
    relative_size: float = NodeTypes.SERVER.value ** 2


class CategoryNode(GraphNode):
    node_type: NodeTypes = NodeTypes.CATEGORY.name.lower()
    val: int = NodeTypes.CATEGORY.value
    relative_size: float = NodeTypes.CATEGORY.value ** 2


class ChannelNode(GraphNode):
    node_type: NodeTypes = NodeTypes.CHANNEL.name.lower()
    val: int = NodeTypes.CHANNEL.value
    relative_size: float = NodeTypes.CHANNEL.value ** 2


class ThreadNode(GraphNode):
    node_type: NodeTypes = NodeTypes.THREAD.name.lower()
    val: int = NodeTypes.THREAD.value
    relative_size: float = NodeTypes.THREAD.value ** 2


class MessageNode(GraphNode):
    node_type: NodeTypes = NodeTypes.MESSAGE.name.lower()
    val: int = NodeTypes.MESSAGE.value
    relative_size: float = NodeTypes.MESSAGE.value ** 2


class TagNode(GraphNode):
    node_type: NodeTypes = NodeTypes.TAG.name.lower()
    val: int = NodeTypes.TAG.value
    relative_size: float = NodeTypes.TAG.value ** 2


class UserNode(GraphNode):
    node_type: NodeTypes = NodeTypes.USER.name.lower()
    val: int = NodeTypes.USER.value
    relative_size: float = NodeTypes.USER.value ** 2


class GraphLink(BaseModel):
    source: str
    target: str

    directional: bool = True

    link_type: LinkTypes = LinkTypes.DEFAULT.name.lower()
    group: int = 0
    relative_length: float = 1.0
    # color: str = "#F5F5F5" # White Smoke
    # metadata: Dict[str, Any] = Field(default_factory=dict)


class ParentLink(GraphLink):
    """
    A link from a parent node to a child, e.g. server -> category, category -> channel, etc.
    """
    link_type: LinkTypes = LinkTypes.PARENT.name.lower()
    directional: bool = True


class TagLink(GraphLink):
    """
    A link between a tag and a message, thread, or other node.
    """
    link_type: LinkTypes = LinkTypes.TAG.name.lower()
    directional: bool = False


class ThreadLink(GraphLink):
    """
    A link between Subsequent messages in a thread., e.g. message1 -> message2, message2 -> message3, etc.
    """
    link_type: LinkTypes = LinkTypes.THREAD.name.lower()
    directional: bool = True


class SemanticLink(GraphLink):
    """
    A link between a node and the location of its semantic embedding XYZ coordinates (derived from t-SNE).
    """
    link_type: LinkTypes = LinkTypes.SEMANTIC.name.lower()
    directional: bool = False


class UserLink(GraphLink):
    """
    A link between a user and the messages the messages and tags associated with them.
    """
    link_type: LinkTypes = LinkTypes.USER.name.lower()
    directional: bool = False


class GraphData(BaseModel):
    """
    https://github.com/vasturiano/3d-force-graph?tab=readme-ov-file#api-reference
    """
    nodes: List[GraphNode]
    links: List[GraphLink]
    # metadata: Dict[str, Any] = Field(default_factory=dict)


if __name__ == "__main__":
    dummy_graph_data = GraphData(
        nodes=[
            GraphNode(id="1", name="Node 1"),
            GraphNode(id="2", name="Node 2"),
            GraphNode(id="3", name="Node 3"),
        ],
        links=[
            GraphLink(source="1", target="2"),
            GraphLink(source="2", target="3"),
        ],
    )
    pprint(dummy_graph_data.model_dump_json(indent=2))
