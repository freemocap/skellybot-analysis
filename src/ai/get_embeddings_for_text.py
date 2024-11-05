from openai import AsyncOpenAI

DEFAULT_EMDEDDINGS_MODEL = "text-embedding-3-small"


async def get_embedding_for_text(client: AsyncOpenAI,
                                 text_to_embed: str,
                                 embedding_model: str = DEFAULT_EMDEDDINGS_MODEL):

    embedding_responses = []
    embedding_max_tokens = 8000
    for i in range(0, len(text_to_embed),
                   embedding_max_tokens):  # really should be splitting by token hgere, but characters are smaller than tokens, so it's fine
        embedding_response = await client.embeddings.create(
            input=text_to_embed[i:i + embedding_max_tokens],
            model=embedding_model
        )
        embedding_responses.append(embedding_response)
    return embedding_responses

if __name__ == "__main__":
    from main_ai_process import OPENAI_CLIENT
    from pprint import pprint
    import asyncio
    text_to_embed = "Once upon a time, there were a bunch a whosits"
    embeddings = asyncio.run(get_embedding_for_text(OPENAI_CLIENT,text_to_embed))
    pprint(embeddings)