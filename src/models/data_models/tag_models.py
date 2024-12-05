from typing import List, TYPE_CHECKING

from pydantic import BaseModel

from src.models.data_models.data_object_model import DataObjectModel
from src.models.data_models.server_data.server_context_route_model import ServerContextRoute

if TYPE_CHECKING:
    from src.models.data_models.server_data.server_data_model import ServerData
    from src.models.data_models.user_data_model import UserDataManager

class TagModel(DataObjectModel):
    tagged_threads: List[DataObjectModel] = []
    tagged_users: List[DataObjectModel] = []

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
    tags_rank_by_thread_count: List[TagStats] = []
    tags_rank_by_user_count: List[TagStats] = []

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

    tags: List[TagModel] = []
    context_route: ServerContextRoute

    @property
    def stats(self):
        return ServerTagStats.from_tag_manager(self)

    @classmethod
    def create(cls, server_data: 'ServerData', user_data: 'UserDataManager'):
        tag_manager = cls(context_route = server_data.context_route)
        for thread in server_data.get_chat_threads():
            tag_manager.extract_tags(thread)
        for user in user_data.users.values():
            tag_manager.extract_tags(user)
        return tag_manager

    def extract_tags(self, thing: DataObjectModel):
        from src.models.data_models.user_data_model import UserData
        from src.models.data_models.server_data.server_data_sub_object_models import ChatThread
        for thing_tag in thing.tags:
            tag = self.get_or_add_tag(thing_tag.id)
            if isinstance(thing, UserData):
                tag.tagged_users.append(thing)
            elif isinstance(thing, ChatThread):
                tag.tagged_thread.append(thing)



    def get_or_add_tag(self, tag_name: str) -> TagModel:
        for tag in self.tags:
            if not isinstance(tag, TagModel):
                raise ValueError("tag is not a TagModel")
            if tag.name == tag_name:
                return tag
        if isinstance(tag_name, str):
            self.tags.append(TagModel.from_tag(tag_name=tag_name, context_route=self.context_route))
        if isinstance(tag_name, TagModel):
            self.tags.append(tag_name)
        return self.get_or_add_tag(tag_name)
