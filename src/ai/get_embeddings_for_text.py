from typing import List

import numpy as np

from openai import AsyncOpenAI

DEFAULT_EMDEDDINGS_MODEL = "text-embedding-3-small"
import logging
logger = logging.getLogger(__name__)
async def get_embedding_for_text(client: AsyncOpenAI,
                                 text_to_embed: str,
                                 embedding_model: str = DEFAULT_EMDEDDINGS_MODEL) -> List[float]:
    embedding_responses = []
    embedding_max_tokens = 8000

    try:
        for i in range(0, len(text_to_embed),
                       embedding_max_tokens):  # really should be splitting by token hgere, but characters are smaller than tokens, so it's fine
            embedding_response = await client.embeddings.create(
                input=text_to_embed[i:i + embedding_max_tokens],
                model=embedding_model
            )
            embedding_responses.append(embedding_response.data[0].embedding)
    except Exception as e:
        logger.exception(f"Error getting embeddings for text: {e}")


    return list(np.mean(embedding_responses, axis=0)) # return mean if multiple embeddings are returned

if __name__ == "__main__":
    from main_ai_process import OPENAI_CLIENT
    from pprint import pprint
    import asyncio
    text_to_embed = "woweee this is a long text, I wonder what the embeddings will look like for this text"
    embeddings = asyncio.run(get_embedding_for_text(OPENAI_CLIENT,text_to_embed))
    pprint(embeddings)