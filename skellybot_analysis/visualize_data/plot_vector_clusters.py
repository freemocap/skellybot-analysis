import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
from plotly.io import write_html

from skellybot_analysis.analysis_scripts.save_db_to_csv import save_db_as_dataframes
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

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


def create_dash_app(df: pd.DataFrame,
                    save_html_path: str) -> Dash:
    logger.info("Creating Dash app for 3D visualization")
    app = Dash(__name__)
    fig = go.Figure()

    # Create sphere coordinates
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)

    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u)) * .95, np.cos(v))

    fig.add_trace(go.Scatter3d(
        x=df['x'],
        y=df['y'],
        z=df['z'],
        mode='markers',
        marker=dict(
            size=5,
            color=df['channel_name'].astype('category').cat.codes,  # Use channel name for color
            colorscale='Viridis',
            opacity=0.8
        ),
        text=df['thread_name'] + '<br>' + df['category_name'],
        hoverinfo='text',
        customdata=df['text_contents'].values,
        name='Threads'
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
        text_contents = point_data['customdata']
        thread_name = point_data['text'].split('<br>')[0]
        return html.Div([
            html.H3(thread_name),
            html.Pre(text_contents)
        ])

    return app




if __name__ == "__main__":
    import asyncio
    _db_path = get_most_recent_db_location()


    # Create visualization dataframe
    _df = asyncio.run(save_db_as_dataframes(db_path=_db_path))

    # Setup output paths
    outer_output_path = Path(_db_path).parent
    html_file_name = Path(_db_path).stem + '_3d_cluster_data_viz.html'
    html_file_path = outer_output_path / html_file_name

    # Create and run the Dash app
    app = create_dash_app(_df, save_html_path=str(html_file_path))
    logger.info(f"Running Dash app server...")
    app.run_server(debug=True, port=8050)
    logger.info(f"Dash app server stopped.")