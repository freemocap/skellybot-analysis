from typing import List, Optional, Dict, Any

from pydantic import Field

from src.models.data_models.data_object_model import DataObjectModel
from src.models.data_models.server_data.server_data_object_types_enum import ServerDataObjectTypes
from src.models.data_models.server_data.server_data_stats import ServerDataStats
from src.models.data_models.server_data.server_data_sub_object_models import ChatThread
from src.models.text_analysis_prompt_model import TextAnalysisPromptModel


class UserData(DataObjectModel):
    id: int
    type: ServerDataObjectTypes = ServerDataObjectTypes.USER
    threads: List[ChatThread] = Field(default_factory=list)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    tag_tsne_xyzs: Dict[str, List[float]] = Field(default_factory=dict)

    def as_text(self) -> str:
        return f"User: {self.id}\n" + "\n".join([thread.as_text() for thread in self.threads])

    def as_full_text(self) -> str:
        return f"User: {self.id}\n" + self.ai_analysis.to_string() + "\n______________\n" + "\n".join(
            [thread.as_text() for thread in self.threads])

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'threads'})

    def stats(self) -> ServerDataStats:
        return ServerDataStats(id=self.id,
                               name=f"User {self.id}",
                               type="User",
                               categories=0,
                               channels=0,
                               threads=len(self.threads),
                               messages=sum([len(thread.messages) for thread in self.threads]),
                               total_words=sum([len(message.content.split()) for thread in self.threads for message in
                                                thread.messages]),
                               human_words=sum([len(message.content.split()) for thread in self.threads for message in
                                                thread.messages if message.is_bot == False]),
                               bot_words=sum([len(message.content.split()) for thread in self.threads for message in
                                              thread.messages if message.is_bot == True])
                               )
