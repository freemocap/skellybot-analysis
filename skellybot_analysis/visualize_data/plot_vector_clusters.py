import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
from plotly.io import write_html

from skellybot_analysis.utilities.get_most_recent_scrape_data import get_server_data

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



def create_dash_app(dfs: dict[str, dict[str, pd.DataFrame]],
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


def save_dataframes_to_json(dfs: dict[str, dict[str, pd.DataFrame]], file_path: str) -> None:
    # Convert each DataFrame to a JSON string
    json_data = {key: {norm_type: df.to_json() for norm_type, df in norm_dict.items()} for key, norm_dict in
                 dfs.items()}

    # Save the JSON string to a file
    with open(file_path, 'w') as f:
        json.dump(json_data, f)


def load_dataframes_from_json(file_path: str) -> dict[str, dict[str, pd.DataFrame]]:
    # Load the JSON string from the file
    with open(file_path, 'r') as f:
        json_data = json.load(f)

    # Convert the JSON string back to DataFrames
    dfs = {key: {norm_type: pd.read_json(df_json) for norm_type, df_json in norm_dict.items()} for key, norm_dict in
           json_data.items()}

    return dfs



if __name__ == "__main__":
    _server_data, _json_path = get_server_data()
    outer_output_path = Path(_json_path).parent
    html_file_name = Path(_json_path).stem + '_3d_cluster_data_viz.html'
    html_file_path = outer_output_path / html_file_name

    app = create_dash_app(_dfs, save_html_path=str(html_file_path))
    logger.info(f"Running Dash app server...")
    app.run_server(debug=True, port=8050)
    logger.info(f"Dash app server stopped.")
