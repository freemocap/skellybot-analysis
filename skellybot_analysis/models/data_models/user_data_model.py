from typing import List, Optional, Dict, Any

from pydantic import Field, BaseModel, computed_field

from skellybot_analysis.models.data_models.data_object_model import DataObjectModel
from skellybot_analysis.models.data_models.server_data.server_data_object_types_enum import ServerDataObjectTypes
from skellybot_analysis.models.data_models.tag_models import TagModel
from skellybot_analysis.models.prompt_models.user_profile_prompt_model import UserProfilePromptModel


class DescriptiveStatistics(BaseModel):
    count: int
    mean: float
    std: float
    min: float
    q1: float
    median: float
    q3: float
    max: float

    @classmethod
    def from_list(cls, data: List[float]):
        data.sort()
        count = len(data)
        mean = sum(data) / count
        std = (sum([(x - mean) ** 2 for x in data]) / count) ** 0.5
        min_val = data[0]
        q1 = data[count // 4]
        median = data[count // 2]
        q3 = data[3 * count // 4]
        max_val = data[-1]
        return cls(count=count, mean=mean, std=std, min=min_val, q1=q1, median=median, q3=q3, max=max_val)


class SingleUserDataStats(BaseModel):
    id: int
    name: str
    type: str
    threads: int
    messages: int
    total_words: int
    human_words: int
    bot_words: int

    @classmethod
    def from_user_data(cls, user_data):
        threads = user_data.threads
        return cls(
            id=user_data.id,
            name=f"User {user_data.id}",
            type="User",
            threads=len(threads),
            messages=sum([len(thread.messages) for thread in threads]),
            total_words=sum([len(message.content.split()) for thread in threads for message in thread.messages]),
            human_words=sum([len(message.content.split()) for thread in threads for message in thread.messages if
                             message.is_bot == False]),
            bot_words=sum([len(message.content.split()) for thread in threads for message in thread.messages if
                           message.is_bot == True])
        )


class ServerUserStats(BaseModel):
    user_count: int
    thread_count_stats: DescriptiveStatistics
    message_count_stats: DescriptiveStatistics
    total_words_by_user: DescriptiveStatistics
    human_words_by_user: DescriptiveStatistics
    bot_words_by_user: DescriptiveStatistics

    user_stats: Dict[int, SingleUserDataStats]

    @classmethod
    def from_user_data(cls, user_data: List['UserData']):
        user_data_stats = {user.id: user.stats for user in user_data}
        return cls(
            user_count=len(user_data),
            thread_count_stats=DescriptiveStatistics.from_list([user.threads for user in user_data_stats.values()]),
            message_count_stats=DescriptiveStatistics.from_list([user.messages for user in user_data_stats.values()]),
            total_words_by_user=DescriptiveStatistics.from_list([user.total_words for user in user_data_stats.values()]),
            human_words_by_user=DescriptiveStatistics.from_list([user.human_words for user in user_data_stats.values()]),
            bot_words_by_user=DescriptiveStatistics.from_list([user.bot_words for user in user_data_stats.values()]),
            user_stats=user_data_stats
        )


class UserData(DataObjectModel):
    id: int
    type: ServerDataObjectTypes = ServerDataObjectTypes.USER
    threads: List[DataObjectModel] = Field(default_factory=list)
    ai_analysis: Optional[UserProfilePromptModel] = None
    tag_tsne_xyzs: Dict[str, List[float]] = Field(default_factory=dict)

    @computed_field()
    @property
    def stats(self) -> SingleUserDataStats:
        return SingleUserDataStats.from_user_data(self)

    @computed_field()
    @property
    def tags(self) -> List[TagModel]:
        if self.ai_analysis is None:
            return []
        return [TagModel.from_tag(tag_name=tag, context_route=self.context_route) for tag in  self.ai_analysis.tags_list]

    def as_ai_prompt_text(self) -> str:
        user_string = f"User: {self.id}\n"
        user_string += f"This user participated in {len(self.threads)} threads on the following topics:\n\n- "
        user_string += "\n- ".join([thread.ai_analysis.extremely_short_summary for thread in self.threads])
        user_string += "\n\n Here are the summaries of the threads:\n\n"
        user_string += "\n\n-----------\n\n-----------\n\n".join(
            [thread.ai_analysis.to_string() for thread in self.threads])
        return user_string

    @computed_field()
    @property
    def as_text(self) -> str:
        if self.ai_analysis is None:
            ai_text = ""
        else:
            ai_text = self.ai_analysis.to_string()
        summary_text = self.as_ai_prompt_text()
        user_text = (f"User: {self.id}\n" + ai_text +
                     "\n\n___________\n\n" +
                     summary_text +
                     "\n\nFULL CHAT THREADS BELOW\n\n".join(
                         [thread.as_text() for thread in self.threads]))
        return user_text

    def model_dump_no_children(self) -> Dict[str, Any]:
        return self.model_dump(exclude={'threads'})




class UserDataManager(BaseModel):
    users: Dict[int, UserData] = Field(default_factory=dict)

    @property
    def stats(self) -> ServerUserStats:
        return ServerUserStats.from_user_data(list(self.users.values()))

    def add_user(self, user: UserData):
        self.users[user.id] = user
