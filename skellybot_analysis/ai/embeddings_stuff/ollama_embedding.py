from typing import List

from ollama import AsyncClient
from tqdm import tqdm

DEFAULT_OLLAMA_EMBEDDINGS_MODEL = "mxbai-embed-large"
async def calculate_ollama_embeddings(texts_to_embed: List[str]) -> List[List[float]]:
    print(f"Calculating embeddings for {len(texts_to_embed)} texts...")
    ollama_client =AsyncClient()
    embeddings = []

    for n, text in enumerate(texts_to_embed):
        embeddings.append(await ollama_client.embed(model=DEFAULT_OLLAMA_EMBEDDINGS_MODEL,
                                  input=text,
                                  truncate=True,
                                  keep_alive=1) #'keep_alive' one second for speed?
        )

    print(f"Succesfully calculated embeddings for {len(embeddings)} texts!")
    return [list(embedding.embeddings[0]) for embedding in embeddings]

if __name__ == "__main__":
    import asyncio
    texts_to_embed = [
        "This is a test sentence.",
        "This is another test sentence.",
        "This is a third test sentence."
    ]
    embeddings = asyncio.run(calculate_ollama_embeddings(texts_to_embed))
    embeddings_lengths = [len(embedding) for embedding in embeddings]
    print(f"embedding lengths: {embeddings_lengths}")
