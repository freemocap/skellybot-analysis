from typing import List
import asyncio

from ollama import AsyncClient

DEFAULT_OLLAMA_EMBEDDINGS_MODEL = "mxbai-embed-large"


async def calculate_ollama_embeddings(texts_to_embed: List[str]) -> List[List[float]]:
    print(f"Calculating embeddings for {len(texts_to_embed)} texts...")
    ollama_client = AsyncClient()
    embeddings = []

    for n, text in enumerate(texts_to_embed):
        if not isinstance(text, str):
            raise ValueError(f"Expected text to be a string, but got {type(text)}")
        embeddings.append(asyncio.create_task(ollama_client.embed(model=DEFAULT_OLLAMA_EMBEDDINGS_MODEL,
                                                                  input=text,
                                                                  truncate=True))
                          )
    embeddings = await asyncio.gather(*embeddings)
    print(f"Succesfully calculated embeddings for {len(embeddings)} texts!")
    return [list(embedding.embeddings[0]) for embedding in embeddings]


if __name__ == "__main__":
    import asyncio

    _texts_to_embed = [
        "This is a test sentence.",
        "This is another test sentence.",
        "This is a third test sentence."
    ]
    _embeddings = asyncio.run(calculate_ollama_embeddings(_texts_to_embed))
    embeddings_lengths = [len(embedding) for embedding in _embeddings]
    print(f"embedding lengths: {embeddings_lengths}")
