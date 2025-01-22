from pydantic import BaseModel

from skellybot_analysis.models.data_models.user_data_model import ServerUserStats


class ServerDataStats(BaseModel):
    id: int
    name: str
    type: str
    categories: int
    channels: int
    threads: int
    messages: int
    total_words: int
    human_words: int
    bot_words: int
    users: ServerUserStats
    # tags: ServerTagStats #TODO - add this back in, but needs happen after ai_analysis
