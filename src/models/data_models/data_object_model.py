from abc import abstractmethod, ABC
from typing import Optional, List

from pydantic import BaseModel, Field

from src.models.data_models.embedding_vector import EmbeddingVector
from src.models.data_models.server_data.server_context_route_model import ServerContextRoute
from src.models.data_models.xyz_data_model import XYZData
from src.models.prompt_models.text_analysis_prompt_model import TextAnalysisPromptModel
from src.models.data_models.tag_models import TagModel


class DataObjectModel(BaseModel, ABC):
    name: str
    id: int
    type: str
    context_route: ServerContextRoute
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embedding: EmbeddingVector | None = None
    tsne_xyz: XYZData | None = None
    tags: List[TagModel] = Field(default_factory=list)

    @abstractmethod
    def as_text(self) -> str:
        pass
