from abc import ABC, abstractmethod
from datetime import datetime

from sqlmodel import SQLModel, Field


class DataObjectModel(SQLModel, ABC):
    id: int = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        # Ensure SQLModel serializes datetime objects correctly
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    # ai_analysis: TextAnalysisPromptModel|None = None
    # embedding: list[list[float]] | None = None
    # tsne_xyz: XYZData | None = None

    # @property
    # def tags(self):
    #     from skellybot_analysis.models.data_models.tag_models import TagModel
    #     if self.ai_analysis is None:
    #         raise ValueError("Cannot get tags from a DataObjectModel until after the AI analysis has been run")
    #     return [TagModel.from_tag(tag_name=tag_name, context_route=self.context_route ) for tag_name in  self.ai_analysis.tags_list]

    @abstractmethod
    def as_text(self) -> str:
        pass
