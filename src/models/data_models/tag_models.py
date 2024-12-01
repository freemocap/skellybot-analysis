from typing import List

from pydantic import BaseModel

from src.models.data_models.embedding_vector import EmbeddingVector
from src.models.data_models.xyz_data_model import XYZData


class TagModel(BaseModel):
    name: str
    id: str
    embedding: EmbeddingVector | None = None
    tsne_xyz: XYZData | None = None
    link_count: int = 0

    @classmethod
    def from_tag(cls, tag_name: str):
        if not tag_name.startswith("#"):
            tag_name = "#" + tag_name
        return cls(name=tag_name, id=tag_name.replace("#", "tag-"))

    def as_text(self) -> str:
        return self.name.replace('#', '').replace('-', ' ')

class TagManager(BaseModel):
    tags: List[TagModel] = []

    def get_tag(self, tag_name: str) -> TagModel:
        for tag in self.tags:
            if tag.name == tag_name:
                return tag
        return TagModel.from_tag(tag_name)

    def add_tag(self, tag_name: str):
        tag = self.get_tag(tag_name)
        if tag not in self.tags:
            self.tags.append(tag)
        else:
            tag.link_count += 1

