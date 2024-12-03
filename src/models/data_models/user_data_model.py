from typing import List, Optional, Dict, Any

from pydantic import Field, BaseModel

from src.models.data_models.data_object_model import DataObjectModel
from src.models.data_models.server_data.server_data_object_types_enum import ServerDataObjectTypes
from src.models.data_models.server_data.server_data_sub_object_models import ChatThread
from src.models.data_models.text_data_stats import TextDataStats
from src.models.prompt_models.text_analysis_prompt_model import TextAnalysisPromptModel


class UserData(DataObjectModel):
    id: int
    type: ServerDataObjectTypes = ServerDataObjectTypes.USER
    threads: List[ChatThread] = Field(default_factory=list)
    ai_analysis: Optional[TextAnalysisPromptModel] = None
    tag_tsne_xyzs: Dict[str, List[float]] = Field(default_factory=dict)

    def as_ai_prompt_text(self) -> str:
        user_string = f"User: {self.id}\n"
        user_string += f"This user participated in {len(self.threads)} threads on the following topics:\n\n- "
        user_string += "\n- ".join([thread.ai_analysis.extremely_short_summary for thread in self.threads])
        user_string += "\n\n Here are the summaries of the threads:\n\n"
        user_string += "\n\n-----------\n\n-----------\n\n".join([thread.ai_analysis.to_string() for thread in self.threads])
        return user_string

    def as_text(self) -> str:
        if self.ai_analysis is None:
            ai_text = ""
        else:
            ai_text = self.ai_analysis.to_string()
        summary_text = self.as_ai_prompt_text()
        user_text= (f"User: {self.id}\n" + ai_text +
                "\n\n___________\n\n" +
                summary_text +
                "\n\nFULL CHAT THREADS BELOW\n\n".join(
            [thread.as_text() for thread in self.threads]))
        return user_text
    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'threads'})

    def stats(self) -> TextDataStats:
        return TextDataStats(id=self.id,
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


class UserDataManager(BaseModel):
    users: Dict[int, UserData] = Field(default_factory=dict)

    def add_user(self, user: UserData):
        self.users[user.id] = user
