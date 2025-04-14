from pydantic import BaseModel

from skellybot_analysis.models.data_models.user_data_model import ServerUserStats


class ServerDataStats(BaseModel):
    id: int
    name: str
    categories: int
    channels: int
    threads: int
    messages: int
    total_words: int
    human_words: int
    bot_words: int
    users: ServerUserStats
