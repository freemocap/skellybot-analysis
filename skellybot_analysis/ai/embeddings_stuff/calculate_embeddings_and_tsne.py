import logging
from pathlib import Path

import numpy as np
from sklearn.manifold import TSNE

from skellybot_analysis.ai.embeddings_stuff.ollama_embedding import calculate_ollama_embeddings
from skellybot_analysis.models.data_models.server_data.server_data_model import Server
from skellybot_analysis.models.data_models.xyz_data_model import XYZData


logger = logging.getLogger(__name__)


async def create_embedding_and_tsne_clusters(server_data: Server):
    logger.info(f"Creating DataFrames for 3D visualization for server named {server_data.name}")

    tsne = TSNE(n_components=3, random_state=2, perplexity=5)
    texts_to_embed = [data_object.as_text() for data_object in server_data.get_all_sub_objects()]

    embedding_vectors = await calculate_ollama_embeddings(texts_to_embed)

    if len(embedding_vectors) == 0:
        logger.error(f"No embeddings found! Skipping t-SNE.")
        raise ValueError(f"No embeddings found!. Skipping t-SNE.")
    embeddings_npy = np.array(embedding_vectors)

    embeddings_3d = tsne.fit_transform(embeddings_npy)

    for index, data_object in enumerate(server_data.get_all_sub_objects()):
        data_object.tsne_xyz = XYZData.from_vector(embeddings_3d[index, :])


if __name__ == "__main__":
    import asyncio
    from skellybot_analysis.utilities.get_most_recent_server_data import get_server_data
    _server_data, server_data_json_path = get_server_data()
    asyncio.run(create_embedding_and_tsne_clusters(_server_data))
    Path(server_data_json_path).write_text(_server_data.model_dump_json(indent=2), encoding="utf-8")