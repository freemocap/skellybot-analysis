import logging

import numpy as np
from pydantic import BaseModel
from sklearn.manifold import TSNE

from skellybot_analysis.ai.embeddings_stuff.ollama_embedding import calculate_ollama_embeddings
from skellybot_analysis.models.xyz_data_model import XYZData

logger = logging.getLogger(__name__)

PerplexityInt = int # Type alias for perplexity integer parameter for t-SNE
class EmbeddingAndTsneXYZ(BaseModel):
    embedding: list[float]
    tsne_xyz:XYZData


async def create_embedding_and_tsne_clusters(texts_to_embed: list[str],
                                             n_components: int = 3,
                                             random_state: int = 2,
                                             perplexity: int = 5) -> list[EmbeddingAndTsneXYZ]:
    logger.info(f"Creating embeddings and t-SNE clusters for {len(texts_to_embed)} texts.")
    if perplexity >= len(texts_to_embed):
        logger.error(f"Perplexity {perplexity} is greater than the number of texts {len(texts_to_embed)}. "
                     f"Setting perplexity to {len(texts_to_embed) - 1}.")
        perplexity = len(texts_to_embed) - 1

    embedding_vectors = await calculate_ollama_embeddings(texts_to_embed)

    if len(embedding_vectors) == 0:
        logger.error(f"No embeddings found! Skipping t-SNE.")
        raise ValueError(f"No embeddings found!. Skipping t-SNE.")
    embeddings_npy = np.array(embedding_vectors)

    tsne = TSNE(n_components=n_components, random_state=random_state, perplexity=perplexity)
    embeddings_3d = tsne.fit_transform(embeddings_npy)
    results = []
    for index, data_object in enumerate(texts_to_embed):
        results.append(EmbeddingAndTsneXYZ(
            embedding=embedding_vectors[index],
            tsne_xyz=XYZData.from_vector(embeddings_3d[index, :])
        ))

    return results

