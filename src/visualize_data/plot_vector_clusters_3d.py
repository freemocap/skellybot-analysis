import logging
import os
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
from sklearn.manifold import TSNE
from src.configure_logging import configure_logging
from src.scrape_server.models.server_data_model import ServerData
from src.utilities.get_most_recent_server_data import get_most_recent_server_data

configure_logging()
logger = logging.getLogger(__name__)


def normalize_rows(arr: np.ndarray) -> np.ndarray:
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


def create_dataframe(server_data: ServerData) -> pd.DataFrame:
    chat_threads = server_data.get_chat_threads()
    embeddings = [thread.embedding for thread in chat_threads]
    embeddings_npy = np.array(embeddings)

    logger.info("Running t-SNE on embeddings")
    tsne = TSNE(n_components=3, random_state=2, perplexity=5)
    embeddings_3d = tsne.fit_transform(embeddings_npy)
    embeddings_3d_normalized = normalize_rows(embeddings_3d)

    logger.info("Creating DataFrame for 3D visualization")
    df = pd.DataFrame(embeddings_3d_normalized, columns=['Dimension 1', 'Dimension 2', 'Dimension 3'])
    df['text_contents'] = [chat_thread.as_full_text() for chat_thread in chat_threads]
    df['category_name'] = [chat_thread.category_name if chat_thread.category_name else 'None' for chat_thread in
                           chat_threads]
    df['channel_name'] = [chat_thread.channel_name for chat_thread in chat_threads]
    df['thread_name'] = [chat_thread.ai_analysis.title for chat_thread in chat_threads]
    return df


def create_dash_app(df: pd.DataFrame):
    app = Dash(__name__)

    fig = px.scatter_3d(
        df,
        x='Dimension 1',
        y='Dimension 2',
        z='Dimension 3',
        color='channel_name',
        symbol='category_name',
        hover_name='thread_name',
        custom_data=['text_contents']
    )

    # Create sphere coordinates
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)

    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u))*.95, np.cos(v))

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


if __name__ == "__main__":
    server_data, json_path = get_most_recent_server_data()
    outer_output_path = Path(json_path).parent
    csv_file_name = Path(json_path).stem + '_3d_cluster_data.csv'
    csv_full_path = outer_output_path / csv_file_name
    if csv_full_path.exists():
        df = pd.read_csv(csv_full_path)
    else:
        df = create_dataframe(server_data)
        df.to_csv(str(csv_full_path))
    app = create_dash_app(df)
    app.run_server(debug=True, port=8050)
