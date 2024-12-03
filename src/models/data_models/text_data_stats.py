from pydantic import BaseModel


class TextDataStats(BaseModel):
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
