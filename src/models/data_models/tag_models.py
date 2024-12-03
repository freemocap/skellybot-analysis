from typing import List

from pydantic import BaseModel

from src.models.data_models.embedding_vector import EmbeddingVector
from src.models.data_models.xyz_data_model import XYZData
from src.models.prompt_models.topic_article_writer_prompt_model import WikipediaStyleArticleWriterModel


class TagModel(BaseModel):
    name: str
    id: str
    embedding: EmbeddingVector | None = None
    ai_analysis: WikipediaStyleArticleWriterModel | None = None
    tsne_xyz: XYZData | None = None
    link_count: int = 0
    tagged_threads: List[str] = []
    tagged_users: List[str] = []

    @classmethod
    def from_tag(cls, tag_name: str):
        if not tag_name.startswith("#"):
            tag_name = "#" + tag_name
        return cls(name=tag_name, id=tag_name.replace("#", "tag-"))

    def as_text(self) -> str:
        return self.name.replace('#', '').replace('-', ' ')

    def __eq__(self, other):
        return self.name == other.name and self.id == other.id

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

