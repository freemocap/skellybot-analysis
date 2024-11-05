from pathlib import Path

import numpy as np
import pandas as pd
from plotly import express as px, io as pio
from sklearn.manifold import TSNE
from src.scrape_server.models.server_data_model import ServerData
from src.visualize_data.plot_vector_clusters_3d import logger, normalize_rows, open_file_path


def visualize_clusters_3d(server_data: ServerData, output_directory: str):
    logger.info("Visualizing clusters in 3D")

    chat_threads = server_data.get_chat_threads()
    embeddings = [thread.embedding for thread in chat_threads]
    embeddings_npy = np.array(embeddings)

    logger.info("Running t-SNE on embeddings")
    tsne = TSNE(n_components=3,
                random_state=2,
                perplexity=5)
    embeddings_3d = tsne.fit_transform(embeddings_npy)
    embeddings_3d_normalized = normalize_rows(embeddings_3d)

    logger.info("Creating DataFrame for 3D visualization")
    df = pd.DataFrame(embeddings_3d_normalized, columns=['Dimension 1', 'Dimension 2', 'Dimension 3'])
    df['text_contents'] = [chat_thread.ai_analysis.very_short_summary for chat_thread in chat_threads]
    df['category_name'] = [chat_thread.category_name if chat_thread.category_name else 'None'
                           for chat_thread in chat_threads]
    df['channel_name'] = [chat_thread.channel_name for chat_thread in chat_threads]
    df['thread_name'] = [chat_thread.ai_analysis.title for chat_thread in chat_threads]

    logger.info("Creating plotly figure")
    fig = px.scatter_3d(df,
                        x='Dimension 1',
                        y='Dimension 2',
                        z='Dimension 3',
                        color='channel_name',
                        symbol='category_name',
                        hover_name='thread_name',
                        hover_data={'text_contents': True}  # Add text_contents to hover data

                        )
    # Customize hovertemplate to display text_contents
    fig.update_traces(
        hovertemplate="<br>".join([
            "Thread: %{hovertext}",
            "Channel: %{marker.color}",
            "Category: %{marker.symbol}",
            "<b>Text Contents:</b> %{customdata[0]}"
        ]),
        customdata=df[['text_contents']]  # Set custom data for hover
    )
    logger.info("Saving plotly figure")
    html_file_path = str(Path(output_directory, 'cluster_visualization_3d.html'))
    pio.write_html(fig, html_file_path)

    logger.info("Showing plotly figure")
    # open html file in default browser
    open_file_path(html_file_path)
