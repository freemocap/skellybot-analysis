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
                                   thread_analyses_df: pd.DataFrame) ->tuple[np.ndarray, pd.DataFrame]:
    """
    Calculate embeddings and various dimensionality reduction techniques (t-SNE, UMAP, PCA)
    for the given messages and thread analyses, with a range of parameters where appropriate.
    
    Returns a tidy dataframe with embeddings and projections.
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
    results_dict = {
        'id': all_ids,
        'content_type': [id_to_type[id] for id in all_ids],
        'text': [texts_to_embed[id] for id in all_ids],
    }
    
    
    # 1. Calculate t-SNE projections for different dimensions and perplexity values
    logger.info("Calculating t-SNE projections...")
    perplexity_values = range(5, 55, 5)
    
    # 2D t-SNE
    for perplexity in perplexity_values:
        logger.info(f"Running 2D t-SNE with perplexity={perplexity}")
        tsne = TSNE(n_components=2, random_state=RANDOM_SEED, perplexity=perplexity)
        tsne_result = tsne.fit_transform(embeddings_npy)
        
        results_dict[f'tsne_2d_p{perplexity}_x'] = tsne_result[:, 0]
        results_dict[f'tsne_2d_p{perplexity}_y'] = tsne_result[:, 1]
    
    # 3D t-SNE
    for perplexity in perplexity_values:
        logger.info(f"Running 3D t-SNE with perplexity={perplexity}")
        tsne = TSNE(n_components=3, random_state=RANDOM_SEED, perplexity=perplexity)
        tsne_result = tsne.fit_transform(embeddings_npy)
        
        results_dict[f'tsne_3d_p{perplexity}_x'] = tsne_result[:, 0]
        results_dict[f'tsne_3d_p{perplexity}_y'] = tsne_result[:, 1]
        results_dict[f'tsne_3d_p{perplexity}_z'] = tsne_result[:, 2]
    
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
            
            results_dict[f'umap_2d_n{n_neighbors}_d{min_dist:.1f}_x'] = umap_result[:, 0]
            results_dict[f'umap_2d_n{n_neighbors}_d{min_dist:.1f}_y'] = umap_result[:, 1]
    
    # 3D UMAP
    for n_neighbors in n_neighbors_values:
        for min_dist in min_dist_values:
            logger.info(f"Running 3D UMAP with n_neighbors={n_neighbors}, min_dist={min_dist}")
            reducer = umap.UMAP(n_components=3, 
                               n_neighbors=n_neighbors, 
                               min_dist=min_dist, 
                               random_state=42)
            umap_result = reducer.fit_transform(embeddings_npy)
            
            results_dict[f'umap_3d_n{n_neighbors}_d{min_dist:.1f}_x'] = umap_result[:, 0]
            results_dict[f'umap_3d_n{n_neighbors}_d{min_dist:.1f}_y'] = umap_result[:, 1]
            results_dict[f'umap_3d_n{n_neighbors}_d{min_dist:.1f}_z'] = umap_result[:, 2]
    
    # 3. Calculate PCA projections (no parameter sweep needed)
    logger.info("Calculating PCA projections...")
    # 2D PCA
    pca_2d = PCA(n_components=2, random_state=42)
    pca_2d_result = pca_2d.fit_transform(embeddings_npy)
    results_dict['pca_2d_x'] = pca_2d_result[:, 0]
    results_dict['pca_2d_y'] = pca_2d_result[:, 1]
    
    # 3D PCA
    pca_3d = PCA(n_components=3, random_state=42)
    pca_3d_result = pca_3d.fit_transform(embeddings_npy)
    results_dict['pca_3d_x'] = pca_3d_result[:, 0]
    results_dict['pca_3d_y'] = pca_3d_result[:, 1]
    results_dict['pca_3d_z'] = pca_3d_result[:, 2]
    
    # Add variance explained by each PCA component
    for i, var in enumerate(pca_2d.explained_variance_ratio_):
        results_dict[f'pca_2d_variance_{i+1}'] = [var] * len(all_ids)
    
    for i, var in enumerate(pca_3d.explained_variance_ratio_):
        results_dict[f'pca_3d_variance_{i+1}'] = [var] * len(all_ids)
    
    # Create the tidy dataframe
    result_df = pd.DataFrame(results_dict)
    
    # Final dataframe with all the information
    logger.info(f"Created dataframe with {len(result_df)} rows and {len(result_df.columns)} columns")
    
    return embeddings_npy, result_df