import logging

import numpy as np
import pandas as pd
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import umap

from skellybot_analysis.ai.embeddings_stuff.ollama_embedding import calculate_ollama_embeddings

logger = logging.getLogger(__name__)
 
RANDOM_SEED = 42

async def calculate_embeddings_and_projections(human_messages_df: pd.DataFrame,
                                   thread_analyses_df: pd.DataFrame) ->tuple[np.ndarray, dict[str, pd.DataFrame]]:
    """
    Calculate embeddings and various dimensionality reduction techniques (t-SNE, UMAP, PCA)
    for the given messages and thread analyses, with a range of parameters where appropriate.
    
    Returns a tuple containing:
    1. numpy array of embeddings
    2. dictionary with separate dataframes for base data, tsne, umap, and pca projections
    """
    logger.info(
        f"Creating embeddings and projections for {len(human_messages_df)} messages and {len(thread_analyses_df)} thread analyses")

    # Create a dictionary mapping IDs to their text content
    texts_to_embed = {}
    id_to_type = {}  # Keep track of whether each ID is a message or thread analysis

    # Add thread analyses
    for _, analysis in thread_analyses_df.iterrows():
        texts_to_embed[analysis['thread_id']] = str(analysis['full_text_no_base_text'])
        id_to_type[analysis['thread_id']] = 'thread_analysis'

    for _, human_messages_df in human_messages_df.iterrows():
        texts_to_embed[human_messages_df['id']] = str(human_messages_df['message_and_response'])
        id_to_type[human_messages_df['id']] = 'message_and_response'

    all_ids = list(texts_to_embed.keys())
    
    # Calculate embeddings
    logger.info("Calculating embeddings...")
    embedding_vectors = await calculate_ollama_embeddings(list(texts_to_embed.values()))
    embeddings_npy = np.array(embedding_vectors)
    
    # Create base dataframe with IDs and embeddings
    base_df = pd.DataFrame({
        'id': all_ids,
        'content_type': [id_to_type[id] for id in all_ids],
        'text': [texts_to_embed[id] for id in all_ids],
    })
    
    # Create separate dataframes for different projection types
    tsne_2d_df = base_df[['id', 'content_type']].copy()
    tsne_3d_df = base_df[['id', 'content_type']].copy()
    umap_2d_df = base_df[['id', 'content_type']].copy()
    umap_3d_df = base_df[['id', 'content_type']].copy()
    pca_df = base_df[['id', 'content_type']].copy()
    
    # 1. Calculate t-SNE projections for different dimensions and perplexity values
    logger.info("Calculating t-SNE projections...")
    perplexity_values = range(5, 55, 5)
    
    # 2D t-SNE
    for perplexity in perplexity_values:
        logger.info(f"Running 2D t-SNE with perplexity={perplexity}")
        tsne = TSNE(n_components=2, random_state=RANDOM_SEED, perplexity=perplexity)
        tsne_result = tsne.fit_transform(embeddings_npy)
        
        tsne_2d_df[f'p{perplexity}_x'] = tsne_result[:, 0]
        tsne_2d_df[f'p{perplexity}_y'] = tsne_result[:, 1]
    
    # 3D t-SNE
    for perplexity in perplexity_values:
        logger.info(f"Running 3D t-SNE with perplexity={perplexity}")
        tsne = TSNE(n_components=3, random_state=RANDOM_SEED, perplexity=perplexity)
        tsne_result = tsne.fit_transform(embeddings_npy)
        
        tsne_3d_df[f'p{perplexity}_x'] = tsne_result[:, 0]
        tsne_3d_df[f'p{perplexity}_y'] = tsne_result[:, 1]
        tsne_3d_df[f'p{perplexity}_z'] = tsne_result[:, 2]
    
    # 2. Calculate UMAP projections with different parameters
    logger.info("Calculating UMAP projections...")
    # UMAP parameters to vary
    n_neighbors_values = [5, 15, 30, 50]
    min_dist_values = [0.1, 0.5, 0.8]
    
    # 2D UMAP
    for n_neighbors in n_neighbors_values:
        for min_dist in min_dist_values:
            logger.info(f"Running 2D UMAP with n_neighbors={n_neighbors}, min_dist={min_dist}")
            reducer = umap.UMAP(n_components=2, 
                                n_neighbors=n_neighbors, 
                                min_dist=min_dist, 
                                random_state=42)
            umap_result = reducer.fit_transform(embeddings_npy)
            
            umap_2d_df[f'n{n_neighbors}_d{min_dist:.1f}_x'] = umap_result[:, 0]
            umap_2d_df[f'n{n_neighbors}_d{min_dist:.1f}_y'] = umap_result[:, 1]
    
    # 3D UMAP
    for n_neighbors in n_neighbors_values:
        for min_dist in min_dist_values:
            logger.info(f"Running 3D UMAP with n_neighbors={n_neighbors}, min_dist={min_dist}")
            reducer = umap.UMAP(n_components=3, 
                               n_neighbors=n_neighbors, 
                               min_dist=min_dist, 
                               random_state=42)
            umap_result = reducer.fit_transform(embeddings_npy)
            
            umap_3d_df[f'n{n_neighbors}_d{min_dist:.1f}_x'] = umap_result[:, 0]
            umap_3d_df[f'n{n_neighbors}_d{min_dist:.1f}_y'] = umap_result[:, 1]
            umap_3d_df[f'n{n_neighbors}_d{min_dist:.1f}_z'] = umap_result[:, 2]
    
    # 3. Calculate PCA projections (no parameter sweep needed)
    logger.info("Calculating PCA projections...")
    # 2D PCA
    pca_2d = PCA(n_components=2, random_state=42)
    pca_2d_result = pca_2d.fit_transform(embeddings_npy)
    pca_df['pca_2d_x'] = pca_2d_result[:, 0]
    pca_df['pca_2d_y'] = pca_2d_result[:, 1]
    
    # 3D PCA
    pca_3d = PCA(n_components=3, random_state=42)
    pca_3d_result = pca_3d.fit_transform(embeddings_npy)
    pca_df['pca_3d_x'] = pca_3d_result[:, 0]
    pca_df['pca_3d_y'] = pca_3d_result[:, 1]
    pca_df['pca_3d_z'] = pca_3d_result[:, 2]
    
    # Add variance explained by each PCA component
    for i, var in enumerate(pca_2d.explained_variance_ratio_):
        pca_df[f'pca_2d_variance_{i+1}'] = var
    
    for i, var in enumerate(pca_3d.explained_variance_ratio_):
        pca_df[f'pca_3d_variance_{i+1}'] = var
    
    # Create dictionary of dataframes
    result_dfs = {
        'base': base_df,
        'tsne_2d': tsne_2d_df,
        'tsne_3d': tsne_3d_df,
        'umap_2d': umap_2d_df,
        'umap_3d': umap_3d_df,
        'pca': pca_df
    }
    
    logger.info(f"Created separate dataframes for each projection type")
    
    return embeddings_npy, result_dfs