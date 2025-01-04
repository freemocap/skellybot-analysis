from typing import List, TYPE_CHECKING

from pydantic import BaseModel, Field

from src.models.data_models.data_object_model import DataObjectModel
from src.models.data_models.server_data.server_context_route_model import ServerContextRoute

if TYPE_CHECKING:
    from src.models.data_models.server_data.server_data_model import ServerData
    from src.models.data_models.user_data_model import UserDataManager

class TagModel(DataObjectModel):
    tagged_threads: List[DataObjectModel] = Field(default_factory=list)
    tagged_users: List[DataObjectModel] = Field(default_factory=list)

    @property
    def link_count(self):
        return len(self.tagged_threads) + len(self.tagged_users)

    @property
    def rank_by_thread_count(self):
        return len(self.tagged_threads)

    @property
    def rank_by_user_count(self):
        return len(self.tagged_users)

    @classmethod
    def from_tag(cls,
                 tag_name: str,
                 context_route: ServerContextRoute):
        if not tag_name.startswith("#"):
            tag_name = "#" + tag_name
        return cls(name=tag_name,
                   type="Tag",
                   context_route=context_route,
                   id=tag_name.replace("#", "tag-"))

    def as_text(self) -> str:
        return self.name.replace('#', '').replace('-', ' ')

    def __eq__(self, other):
        return self.name == other.name and self.id == other.id

class TagStats(BaseModel):
    tag: str
    link_count: int

class ServerTagStats(BaseModel):
    """
    Show tags in descending order of link count
    """
    tags_rank_by_thread_count: List[TagStats] = Field(default_factory=list)
    tags_rank_by_user_count: List[TagStats] = Field(default_factory=list)

    @classmethod
    def from_tag_manager(cls, tag_manager):
        server_tag_stats = cls()
        server_tag_stats.tags_rank_by_thread_count = sorted(
            [TagStats(tag=tag.name, link_count=len(tag.tagged_threads)) for tag in tag_manager.tags],
            key=lambda x: x.link_count, reverse=True)
        server_tag_stats.tags_rank_by_user_count = sorted(
            [TagStats(tag=tag.name, link_count=len(tag.tagged_users)) for tag in tag_manager.tags],
            key=lambda x: x.link_count, reverse=True)
        return server_tag_stats


class TagManager(BaseModel):

    tags: List[TagModel] = Field(default_factory=list)
    context_route: ServerContextRoute

    @property
    def stats(self):
        return ServerTagStats.from_tag_manager(self)

    @classmethod
    def create(cls, server_data: 'ServerData', user_data: 'UserDataManager'):
        tag_manager = cls(context_route = server_data.context_route)
        for thread in server_data.get_chat_threads():
            tag_manager.extract_thread_tags(thread)
        for user in user_data.users.values():
            tag_manager.extract_user_tags(user)

        return tag_manager

    def extract_thread_tags(self, thread: DataObjectModel):
        for thread_tag in thread.tags:
            tag = self.get_or_add_tag(thread_tag)
            if thread not in tag.tagged_threads:
                tag.tagged_threads.append(thread)

    def extract_user_tags(self, user: DataObjectModel):
        for user_tag in user.tags:
            tag = self.get_or_add_tag(user_tag)
            if user not in tag.tagged_users:
                tag.tagged_users.append(user)

    def get_or_add_tag(self, query_tag: TagModel) -> TagModel:
        for tag in self.tags:
            if not isinstance(tag, TagModel):
                raise ValueError("tag is not a TagModel")
            if tag == query_tag:
                return tag
        self.tags.append(query_tag)
        return self.get_or_add_tag(query_tag)

