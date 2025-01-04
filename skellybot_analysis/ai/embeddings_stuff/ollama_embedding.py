import asyncio
from typing import List
from tqdm import tqdm
import ollama

DEFAULT_OLLAMA_EMBEDDINGS_MODEL = "mxbai-embed-large"
def calculate_ollama_embeddings(texts_to_embed: List[str]) -> List[List[float]]:
    print(f"Calculating embeddings for {len(texts_to_embed)} texts...")
    embeddings = [
        ollama.embeddings(model=DEFAULT_OLLAMA_EMBEDDINGS_MODEL, prompt=text, keep_alive=1) #'keep_alive' one second for speed?
        for n, text in enumerate(tqdm(texts_to_embed, desc="Calculating embeddings"))
    ]
    print(f"Succesfully calculated embeddings for {len(embeddings)} texts!")
    return [embedding['embedding'] for embedding in embeddings]

if __name__ == "__main__":

    texts_to_embed = [
        "This is a test sentence.",
        "This is another test sentence.",
        "This is a third test sentence."
    ]
    embeddings = calculate_ollama_embeddings(texts_to_embed)
    embeddings_lengths = [len(embedding) for embedding in embeddings]
    print(embeddings_lengths)