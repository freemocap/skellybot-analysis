from abc import abstractmethod, ABC

from pydantic import BaseModel

from skellybot_analysis.models.data_models.server_data.server_context_route_model import ServerContextRoute
from skellybot_analysis.models.data_models.xyz_data_model import XYZData
from skellybot_analysis.models.prompt_models.text_analysis_prompt_model import TextAnalysisPromptModel


class DataObjectModel(BaseModel, ABC):
    name: str
    id: int | str  # unique id
    type: str
    context_route: ServerContextRoute
    ai_analysis: TextAnalysisPromptModel|None = None
    embedding: list[list[float]] | None = None
    tsne_xyz: XYZData | None = None

    @property
    def tags(self):
        from skellybot_analysis.models.data_models.tag_models import TagModel
        if self.ai_analysis is None:
            raise ValueError("Cannot get tags from a DataObjectModel until after the AI analysis has been run")
        return [TagModel.from_tag(tag_name=tag_name, context_route=self.context_route ) for tag_name in  self.ai_analysis.tags_list]

    @abstractmethod
    def as_text(self) -> str:
        pass
