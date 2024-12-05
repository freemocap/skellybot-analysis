from abc import ABC, abstractmethod
from typing import List

from pydantic import Field

from src.models.data_models.data_object_model import DataObjectModel
from src.models.data_models.tag_models import TagModel


class TaggableDataObjectModel(DataObjectModel, ABC):
    tags: List[TagModel] = Field(default_factory=list)

    @property
    def name_id(self) -> str:
        return f"{self.name}-{self.id}"

    @abstractmethod
    def as_text(self) -> str:
        pass
