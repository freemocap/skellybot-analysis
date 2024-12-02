from typing import List

from pydantic import BaseModel


class EmbeddingVector(BaseModel):
    source: str
    embedding: List[float]
