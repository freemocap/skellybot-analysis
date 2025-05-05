import enum
import logging

import numpy as np
import pandas as pd
import umap
from pydantic import BaseModel
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from skellybot_analysis.ai.embeddings_stuff.ollama_embedding import DEFAULT_OLLAMA_EMBEDDINGS_MODEL, \
    calculate_ollama_embeddings
from skellybot_analysis.data_models.analysis_models import AiThreadAnalysisModel

logger = logging.getLogger(__name__)

RANDOM_SEED = 42

# one row per embedded item
# all in the same 
# embeddable items: human+bot messages, thread analyses, tags, user-profile
# columns: 
#   - id (index),
#   - content_type(enum: message_and_response, thread_analysis, tag, user_profile), 
#   - embedded_text, 
#   - thread_id (nullable - for messages and thread analyses),
#   - message_id (nullable, messages only, id of the human message),
#   - user_id (nullable, for everything but tags)
#   - embedding method: str
#   - pca.{component-number}.value, pca.{component-number}.variance, pca.2.value, pca.2.variance, pca.3.value, pca.3.variance (up to 10 components)
#   - tsne.{perplexity-number}.{dimension-number) (perplexity=5-50 in increments of 5), 
#   - umap.{n_neighbors-number}.{min_dist-number}.{dimension-number} (n_neighbors=5-50 in increments of 5, min_dist=0.1-5.0 in increments of 0.5)

class EmbeddableContentType(enum.Enum):
    MESSAGE_AND_RESPONSE = "message_and_response"
    THREAD_ANALYSIS = "thread_analysis"
    TAG = "tag"
    USER_PROFILE = "user_profile"

PCAComponentNumber = int
TSNEPerpexityValue = int
UMAPNeighborsValue = int
UMAPMinDistValue = float

class PCAComponent(BaseModel):
    component_number: PCAComponentNumber
    value: float
    variance_explained: float

class TSNEProjection(BaseModel):
    perplexity: TSNEPerpexityValue
    seed: int
    x: float
    y: float
    z: float

class UMAPProjection(BaseModel):
    n_neighbors: UMAPNeighborsValue
    min_dist: UMAPMinDistValue
    seed: int
    x: float
    y: float
    z: float


class EmbeddableItem(BaseModel):
    embedding_index: int  # Index of the item in the embeddings npy array
    content_type: str  # Enum: message_and_response, thread_analysis, tag, user_profile
    embedded_text: str
    message_id: int | None = None  # for messages only
    thread_id: int | None = None  # messages and thread analyses
    user_id: int | None = None  # for everything but tags
    jump_url: str | None = None  # Jump URL to the relevant thing, if available
    embedding_method: str = DEFAULT_OLLAMA_EMBEDDINGS_MODEL # Default embedding method
    
    pca: dict[PCAComponentNumber, PCAComponent] = {}
    tsne: dict[TSNEPerpexityValue,TSNEProjection] = {}
    umap: dict[UMAPNeighborsValue, dict[UMAPMinDistValue, UMAPProjection]] = {}  # List of UMAP 3D projections

    @classmethod
    def from_human_message_row(cls, df_row: pd.Series, index: int, embedding_method: str = DEFAULT_OLLAMA_EMBEDDINGS_MODEL) -> "EmbeddableItem":
        return cls(
            embedding_index=index,
            content_type=EmbeddableContentType.MESSAGE_AND_RESPONSE.value,
            embedded_text=df_row["message_and_response"],
            message_id=df_row["message_id"],
            thread_id=df_row["thread_id"],
            user_id=df_row["author_id"],
            embedding_method=embedding_method
        )
    
    @classmethod
    def from_thread_analysis(cls, analysis: AiThreadAnalysisModel, index: int, embedding_method: str = DEFAULT_OLLAMA_EMBEDDINGS_MODEL) -> "EmbeddableItem":
        return cls(
            embedding_index=index,
            content_type=EmbeddableContentType.THREAD_ANALYSIS.value,
            embedded_text=analysis.full_text_no_base_text,
            thread_id=analysis.thread_id,
            user_id=analysis.thread_owner_id,
            jump_url=analysis.jump_url,
            embedding_method=embedding_method
        )
    
    @classmethod
    def from_tag(cls, tag: str, index: int, embedding_method: str = DEFAULT_OLLAMA_EMBEDDINGS_MODEL) -> "EmbeddableItem":
        tag_string = tag.replace("#", "").replace("-", " ").replace(",", " ")
        if not tag_string or len(tag_string) < 4:
            raise ValueError(f"Tag '{tag}' is too short or empty after processing.")
        return cls(
            embedding_index=index,
            content_type=EmbeddableContentType.TAG.value,
            embedded_text=tag_string,
            embedding_method=embedding_method
        )

    def model_dump_flattened(self) -> dict:
        """Flatten projections for CSV storage"""
        dump = self.model_dump()

        # Flatten TSNE
        for perplexity, proj in self.tsne.items():
            dump[f"tsne_{perplexity}_x"] = proj.x
            dump[f"tsne_{perplexity}_y"] = proj.y
            dump[f"tsne_{perplexity}_z"] = proj.z

        # Flatten UMAP
        for n_neighbors, dists in self.umap.items():
            for min_dist, proj in dists.items():
                # Use underscore instead of decimal point for column names
                min_dist_str = str(min_dist).replace('.', '_')
                key = f"umap_{n_neighbors}_{min_dist_str}"
                dump[f"{key}_x"] = proj.x
                dump[f"{key}_y"] = proj.y
                dump[f"{key}_z"] = proj.z

        # Flatten PCA
        for comp_num, component in self.pca.items():
            dump[f"pca_{comp_num}_value"] = component.value
            dump[f"pca_{comp_num}_var"] = component.variance_explained

        return dump

async def calculate_embeddings_and_projections(embeddable_items:list[EmbeddableItem]) -> tuple[list[EmbeddableItem], pd.DataFrame]:

    logger.info(f"Creating embeddings and projections for {len(embeddable_items)} items...")

    for index, item in enumerate(embeddable_items):
        if not item.embedding_index == index:
            raise ValueError(
                f"Item index {item.embedding_index} does not match expected index {index}.")
        
    text_to_embed = [item.embedded_text for item in embeddable_items]
    # Calculate embeddings
    logger.info("Calculating embeddings...")
    embedding_vectors = await calculate_ollama_embeddings(text_to_embed)
    embeddings_npy = np.array(embedding_vectors)

    # 1. Calculate t-SNE projections
    logger.info("Calculating t-SNE projections...")
        
    for perplexity in np.arange(5, 55, 5).tolist():  # Perplexity values from 5 to 50 in increments of 5
        logger.info(f"Running 3D t-SNE with perplexity={perplexity}")
        tsne = TSNE(n_components=3, random_state=RANDOM_SEED, perplexity=perplexity)
        tsne_result = tsne.fit_transform(embeddings_npy)
        for item, tsne_result in zip(embeddable_items, tsne_result):
            item.tsne[perplexity] = TSNEProjection(
                perplexity=perplexity,
                seed=RANDOM_SEED,
                x=tsne_result[0],
                y=tsne_result[1],
                z=tsne_result[2]
            )                

    # 2. Calculate UMAP projections
    logger.info("Calculating UMAP projections...")
    # UMAP parameters

    for n_neighbors in np.arange(5, 55, 5).tolist():  # n_neighbors values from 5 to 50 in increments of 5
        for min_dist in np.arange(0.1, 1.0, 0.1).tolist():  # min_dist values from 0.1 to 0.9 in increments of 0.1
            logger.info(f"Running 3D UMAP with n_neighbors={n_neighbors}, min_dist={min_dist}")    
    
    
            reducer = umap.UMAP(n_components=3, n_neighbors=n_neighbors, min_dist=min_dist, random_state=RANDOM_SEED)
            umap_result = reducer.fit_transform(embeddings_npy)
            for item, umap_result in zip(embeddable_items, umap_result):
                if not item.umap.get(n_neighbors):
                    item.umap[n_neighbors] = {}
                item.umap[n_neighbors][min_dist] = UMAPProjection(
                    n_neighbors=n_neighbors,
                    min_dist=min_dist,
                    seed=RANDOM_SEED,
                    x=umap_result[0],
                    y=umap_result[1],
                    z=umap_result[2]
                )
    

    # 3. Calculate PCA projections
    logger.info("Calculating PCA projections...")
    
    # 3D PCA
    pca = PCA(n_components=10, random_state=RANDOM_SEED)
    pca_result = pca.fit_transform(embeddings_npy)
    for item, pca_result in zip(embeddable_items, pca_result):
        item.pca[3] = PCAComponent(
            component_number=3,
            value=pca_result[0],
            variance_explained=pca.explained_variance_ratio_[0]
        )

    embedding_projections_df: pd.DataFrame  = pd.DataFrame(
        [item.model_dump_flattened() for item in embeddable_items]
    )
    return embeddable_items, embedding_projections_df
    