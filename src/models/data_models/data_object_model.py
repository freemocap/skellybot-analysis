from abc import abstractmethod, ABC
from typing import Optional

from pydantic import BaseModel

from src.models.data_models.embedding_vector import EmbeddingVector
from src.models.data_models.server_data.server_context_route_model import ServerContextRoute
from src.models.data_models.xyz_data_model import XYZData
from src.models.prompt_models.text_analysis_prompt_model import TextAnalysisPromptModel


class DataObjectModel(BaseModel, ABC):
    name: str
    id: int | str  # unique id
    type: str
    context_route: ServerContextRoute
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    embedding: EmbeddingVector | None = None
    tsne_xyz: XYZData | None = None

    @property
    def name_id(self) -> str:
        return f"{self.name}-{self.id}"

    @abstractmethod
    def as_text(self) -> str:
        pass
