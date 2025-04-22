import logging
from pathlib import Path

import numpy as np
from sklearn.manifold import TSNE

from skellybot_analysis.ai.embeddings_stuff.ollama_embedding import calculate_ollama_embeddings
from skellybot_analysis.models.xyz_data_model import XYZData


logger = logging.getLogger(__name__)


async def create_embedding_and_tsne_clusters(texts_to_embed: list[str]):
    logger.info(f"Creating embeddings and t-SNE clusters for {len(texts_to_embed)} texts.")

    tsne = TSNE(n_components=3, random_state=2, perplexity=5)

    embedding_vectors = await calculate_ollama_embeddings(texts_to_embed)

    if len(embedding_vectors) == 0:
        logger.error(f"No embeddings found! Skipping t-SNE.")
        raise ValueError(f"No embeddings found!. Skipping t-SNE.")
    embeddings_npy = np.array(embedding_vectors)

    embeddings_3d = tsne.fit_transform(embeddings_npy)
    tsne_xyzs = []
    for index, data_object in enumerate(texts_to_embed):
        tsne_xyzs.append(XYZData.from_vector(embeddings_3d[index, :]))


if __name__ == "__main__":
    import asyncio
    from skellybot_analysis.utilities.get_most_recent_scrape_data import get_server_data
    _server_data, server_data_json_path = get_server_data()
    asyncio.run(create_embedding_and_tsne_clusters(_server_data))
    Path(server_data_json_path).write_text(_server_data.model_dump_json(indent=2), encoding="utf-8")