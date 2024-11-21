from enum import Enum
from pprint import pprint
from typing import List

from pydantic import BaseModel


class NodeTypes(Enum):
    SERVER: float = 5
    CATEGORY: float = 4
    CHANNEL: float = 3
    THREAD: float = 2
    MESSAGE: float = 1
    DEFAULT: float = 0

class GraphNode(BaseModel):

    id: str
    name: str

    root: bool = False
    # children: List[str] = [] # List of node IDs
    # links: List[str] = [] # List of link IDs

    type: str = NodeTypes.DEFAULT.name.lower()
    level: int = NodeTypes.DEFAULT.value
    group: int = 0
    relative_size: float = 1.0
    # color: str = "#F8F8FF" # Ghost White
    # metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphLink(BaseModel):
    source: str
    target: str

    directional: bool = True

    type: str = "default"
    group: int = 0
    relative_strength: float = 1.0
    # color: str = "#F5F5F5" # White Smoke
    # metadata: Dict[str, Any] = Field(default_factory=dict)


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
