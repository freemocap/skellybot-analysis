import json
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
from plotly.io import write_html
from sklearn.manifold import TSNE

from src.configure_logging import configure_logging
from src.scrape_server.models.server_data_model import ServerData
from src.utilities.get_most_recent_server_data import get_server_data

configure_logging()
logger = logging.getLogger(__name__)


def normalize_rows(arr: np.ndarray) -> np.ndarray:
    logger.info("Normalizing rows of array with shape: " + str(arr.shape))
    # Calculate the L2 norm (Euclidean norm) for each row
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    # Avoid division by zero
    norms[norms == 0] = 1
    # Divide each row by its norm
    normalized_array = arr / norms
    return normalized_array


def open_file_path(path: str) -> None:
    """
    Opens a file or directory using the default application on the host operating system.

    :param path: The file or directory path to open.
    """
    logger.info(f"Opening file path: {path}")
    try:
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', path])
        else:  # Linux and other Unix-like systems
            subprocess.run(['xdg-open', path])
    except Exception as e:
        logger.error(f"Failed to open file path: {path}")
        logger.exception(e)
        raise


def create_dataframes(server_data: ServerData) -> Dict[str, Dict[str, pd.DataFrame]]:
    logger.info(f"Creating DataFrames for 3D visualization for server named {server_data.name}")
    data_types = {
        'by_chats': server_data.get_chat_threads(),
        'by_categories': server_data.get_categories(),
        'by_channels': server_data.get_channels(),
        'by_users': server_data.get_chats_by_user()
    }

    dfs = {}
    tsne = TSNE(n_components=3, random_state=2, perplexity=5)

    for key, data in data_types.items():
        logger.info(f"Processing {key} data with {len(data)} items")
        embedding_vectors = []
        for item in data:
            if hasattr(item, 'embedding') and item.embedding:
                embedding_vectors.append(item.embedding)
            else:
                logger.warning(f"{key} item named: `{item.name}` has no embedding data.")
        embeddings_npy = np.array(embedding_vectors)

        if embeddings_npy.size == 0:
            logger.warning(f"No embeddings found for {key}. Skipping t-SNE.")
            continue

        logger.info(f"Running t-SNE on {key} embeddings")
        embeddings_3d = tsne.fit_transform(embeddings_npy)
        embeddings_3d_normalized = normalize_rows(embeddings_3d)

        logger.info(f"Creating DataFrame for 3D visualization for {key}")
        dfs[key] = {}
        for norm_type, embds in {'raw': embeddings_3d,
                                 'normalized': embeddings_3d_normalized}.items():
            dfs[key][norm_type] = pd.DataFrame(embds, columns=['Dimension 1', 'Dimension 2', 'Dimension 3'])

            dfs[key][norm_type]['text_contents'] = [item.as_full_text() for item in data]
            dfs[key][norm_type]['name'] = [item.name if hasattr(item, 'name') else 'None' for item in data]
            dfs[key][norm_type]['ai_title'] = [item.ai_analysis.title for item in data]
            dfs[key][norm_type]['ai_summary'] = [item.ai_analysis.very_short_summary for item in data]
            dfs[key][norm_type]['tags'] = [item.tags for item in data]
            dfs[key][norm_type]['relevant'] = [item.relevant for item in data]

            if key == 'by_chats':
                dfs[key][norm_type]['category_name'] = [item.category_name if item.category_name else 'None' for item in
                                                        data]
                dfs[key][norm_type]['channel_name'] = [item.channel_name for item in data]

            if key == 'by_channels':
                dfs[key][norm_type]['category_name'] = [item.category_name for item in data]

            if key == 'by_users':
                dfs[key][norm_type]['user_id'] = [item.user_id for item in data]
                dfs[key][norm_type]['stats'] = [item.stats for item in data]

    logger.info(f"DataFrames created for 3D visualization for server named {server_data.name}")

    return dfs


def create_dash_app(dfs: Dict[str, Dict[str, pd.DataFrame]],
                    save_html_path: str) -> Dash:
    logger.info("Creating Dash app for 3D visualization")
    app = Dash(__name__)
    df = dfs['by_chats']['normalized']
    fig = go.Figure()

    # Create sphere coordinates
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)

    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u)) * .95, np.cos(v))

    fig.add_trace(go.Scatter3d(
        x=df['Dimension 1'],
        y=df['Dimension 2'],
        z=df['Dimension 3'],
        color=df['channel_name'],
        symbol=df['category_name'],
        hover_name=df['thread_name'],
        custom_data=df['text_contents']
    ))

    # Add sphere to the figure
    fig.add_trace(go.Mesh3d(
        x=x.flatten(),
        y=y.flatten(),
        z=z.flatten(),
        opacity=0.6,
        color='white',
        alphahull=0,
        flatshading=True,
        hoverinfo='skip',
        contour=dict(
            show=True,
            color='black',
            width=1
        )
    ))

    if save_html_path:
        write_html(fig, save_html_path)
        logger.info(f"Plot saved as HTML to {save_html_path}")

    app.layout = html.Div([
        dcc.Graph(id='3d-scatter-plot',
                  figure=fig,
                  style={'width': '70vw',
                         'height': '100vh',
                         'border': '2px solid black'
                         }),

        html.Div(id='hover-data',
                 style={'whiteSpace': 'pre-wrap',
                        'border': '1px solid black',
                        'padding': '2px',
                        'height': '100vh',
                        'width': '30vw',
                        'position': 'absolute',
                        'top': '10px',
                        'right': '10px',
                        'backgroundColor': 'white',
                        'zIndex': 10,
                        'overflow': 'auto'
                        })
    ])

    @app.callback(
        Output('hover-data', 'children'),
        [Input('3d-scatter-plot', 'hoverData')]
    )
    def display_hover_data(hoverData):
        if hoverData is None:
            return "Hover over a point to see details here."

        point_data = hoverData['points'][0]
        text_contents = point_data['customdata'][0]
        return f"Text Contents:\n{text_contents}"

    return app


def save_dataframes_to_json(dfs: Dict[str, Dict[str, pd.DataFrame]], file_path: str) -> None:
    # Convert each DataFrame to a JSON string
    json_data = {key: {norm_type: df.to_json() for norm_type, df in norm_dict.items()} for key, norm_dict in
                 dfs.items()}

    # Save the JSON string to a file
    with open(file_path, 'w') as f:
        json.dump(json_data, f)


def load_dataframes_from_json(file_path: str) -> Dict[str, Dict[str, pd.DataFrame]]:
    # Load the JSON string from the file
    with open(file_path, 'r') as f:
        json_data = json.load(f)

    # Convert the JSON string back to DataFrames
    dfs = {key: {norm_type: pd.read_json(df_json) for norm_type, df_json in norm_dict.items()} for key, norm_dict in
           json_data.items()}

    return dfs


if __name__ == "__main__":
    server_data, json_path = get_server_data()
    outer_output_path = Path(json_path).parent
    cluster_json_file_name = Path(json_path).stem + '_3d_cluster_data.json'
    cluster_csv_full_path = outer_output_path / cluster_json_file_name
    html_file_name = Path(json_path).stem + '_3d_cluster_data_viz.html'
    html_file_path = outer_output_path / html_file_name
    if cluster_csv_full_path.exists() or False:
        dfs = load_dataframes_from_json(str(cluster_csv_full_path))
    else:
        dfs = create_dataframes(server_data)
        save_dataframes_to_json(dfs, str(cluster_csv_full_path))

    app = create_dash_app(dfs, save_html_path=str(html_file_path))
    logger.info(f"Running Dash app server...")
    app.run_server(debug=True, port=8050)
    logger.info(f"Dash app server stopped.")
