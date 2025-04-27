import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.subplots as sp
from dash import Dash, dcc, html, Input, Output, callback_context
import plotly.express as px

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


def create_dash_app(embedding_dfs: dict[str, pd.DataFrame], base_df: pd.DataFrame, save_html_path: str = None) -> Dash:
    logger.info("Creating Dash app for visualizing embeddings")
    app = Dash(__name__, suppress_callback_exceptions=True)

    
    # Extract parameter values from DataFrame column names
    tsne_2d_df = embedding_dfs.get('tsne_2d', pd.DataFrame())
    tsne_3d_df = embedding_dfs.get('tsne_3d', pd.DataFrame())
    umap_2d_df = embedding_dfs.get('umap_2d', pd.DataFrame())
    umap_3d_df = embedding_dfs.get('umap_3d', pd.DataFrame())
    pca_df = embedding_dfs.get('pca', pd.DataFrame())
    
    # Extract perplexity values for t-SNE
    tsne_perplexity_values = []
    if not tsne_2d_df.empty:
        tsne_cols = [col for col in tsne_2d_df.columns if col.startswith('p') and '_x' in col]
        if tsne_cols:
            tsne_perplexity_values = sorted([int(col.split('_')[0][1:]) for col in tsne_cols])
    
    # Extract n_neighbors and min_dist values for UMAP
    umap_n_neighbors = []
    umap_min_dist = []
    if not umap_2d_df.empty:
        umap_cols = [col for col in umap_2d_df.columns if col.startswith('n') and '_x' in col]
        if umap_cols:
            umap_n_neighbors = sorted(list(set([int(col.split('_')[0][1:]) for col in umap_cols])))
            umap_min_dist = sorted(list(set([float(col.split('_')[1][1:]) for col in umap_cols])))
    
    # Get unique user IDs for coloring
    if 'author_id' in base_df.columns:
        user_ids = base_df['author_id'].unique()
    elif 'thread_owner_id' in base_df.columns:
        user_ids = base_df['thread_owner_id'].unique()
    else:
        user_ids = []
        
    # Create layout
    app.layout = html.Div([
        html.H1("Embedding Visualizations"),
        
        html.Div([
            html.Div([
                html.Label("Embedding Method:"),
                dcc.RadioItems(
                    id='embedding-method',
                    options=[
                        {'label': 't-SNE', 'value': 'tsne'},
                        {'label': 'UMAP', 'value': 'umap'},
                        {'label': 'PCA', 'value': 'pca'}
                    ],
                    value='tsne',
                    labelStyle={'display': 'inline-block', 'margin-right': '10px'}
                ),
            ], style={'padding': '10px'}),
            
            html.Div(id='parameter-controls', style={'padding': '10px'}),
        ]),
        
        html.Div([
            dcc.Graph(id='visualization-plot', style={'height': '80vh'})
        ]),
        
        html.Div(id='hover-data', style={
            'whiteSpace': 'pre-wrap',
            'border': '1px solid black',
            'padding': '10px',
            'marginTop': '10px',
            'maxHeight': '300px',
            'overflow': 'auto'
        })
    ])
    @app.callback(
    Output('parameter-controls', 'children'),
    [Input('embedding-method', 'value')]
    )
    def update_parameter_controls(method):
        if method == 'tsne':
            if tsne_perplexity_values:
                return html.Div([
                    html.Label("t-SNE Perplexity:"),
                    dcc.Slider(
                        id='tsne-perplexity',
                        min=min(tsne_perplexity_values),
                        max=max(tsne_perplexity_values),
                        value=tsne_perplexity_values[0],
                        marks={str(val): str(val) for val in tsne_perplexity_values},
                        step=None
                    )
                ])
            else:
                return html.Div([
                    html.P("No t-SNE embeddings available with perplexity parameters.")
                ])
        elif method == 'umap':
            if umap_n_neighbors and umap_min_dist:
                return html.Div([
                    html.Div([
                        html.Label("UMAP n_neighbors:"),
                        dcc.Slider(
                            id='umap-n-neighbors',
                            min=min(umap_n_neighbors),
                            max=max(umap_n_neighbors),
                            value=umap_n_neighbors[0],
                            marks={str(val): str(val) for val in umap_n_neighbors},
                            step=None
                        )
                    ], style={'margin-bottom': '20px'}),
                    
                    html.Div([
                        html.Label("UMAP min_dist:"),
                        dcc.Slider(
                            id='umap-min-dist',
                            min=min(umap_min_dist),
                            max=max(umap_min_dist),
                            value=umap_min_dist[0],
                            marks={str(val): str(val) for val in umap_min_dist},
                            step=None
                        )
                    ])
                ])
            else:
                return html.Div([
                    html.P("No UMAP embeddings available with n_neighbors and min_dist parameters.")
                ])
        elif method == 'pca':
            return html.Div([
                html.P("PCA has no additional parameters to adjust.")
            ])
        return html.Div()
    


    @app.callback(
        Output('visualization-plot', 'figure'),
        [Input('embedding-method', 'value')],
        [Input('parameter-controls', 'children')]
    )
    def update_graph(method, _):
        # Use callback_context to get the current values of the sliders if they exist
        ctx = callback_context
        
        # Initialize default values
        tsne_perplexity = tsne_perplexity_values[0] if tsne_perplexity_values else None
        umap_n_neighbor = umap_n_neighbors[0] if umap_n_neighbors else None
        umap_min_dist_val = umap_min_dist[0] if umap_min_dist else None
        
        # Try to get slider values if they exist in the current layout
        for id_val in ['tsne-perplexity', 'umap-n-neighbors', 'umap-min-dist']:
            try:
                component_value = ctx.inputs.get(f'{id_val}.value')
                if id_val == 'tsne-perplexity' and component_value is not None:
                    tsne_perplexity = component_value
                elif id_val == 'umap-n-neighbors' and component_value is not None:
                    umap_n_neighbor = component_value
                elif id_val == 'umap-min-dist' and component_value is not None:
                    umap_min_dist_val = component_value
            except:
                pass  # Component doesn't exist in the current layout
        
        # Create a 1x2 subplot grid (2D and 3D side by side)
        fig = sp.make_subplots(
            rows=1, cols=2,
            specs=[[{'type': 'xy'}, {'type': 'scene'}]],
            subplot_titles=(f"{method.upper()} 2D", f"{method.upper()} 3D"),
            horizontal_spacing=0.05
        )
        
        # Process color values - convert categorical values to numeric indices
        if 'author_id' in base_df.columns:
            color_column = 'author_id'
            categories = base_df[color_column].astype('category')
            color_values = categories.cat.codes  # Convert to numeric codes
            color_title = 'Author ID'
        elif 'thread_owner_id' in base_df.columns:
            color_column = 'thread_owner_id'
            categories = base_df[color_column].astype('category')
            color_values = categories.cat.codes  # Convert to numeric codes
            color_title = 'Thread Owner ID'
        elif 'content_type' in base_df.columns:
            color_column = 'content_type'
            categories = base_df[color_column].astype('category')
            color_values = categories.cat.codes  # Convert to numeric codes
            color_title = 'Content Type'
        else:
            # Default fallback if no suitable column found
            color_values = None
            color_column = None
            color_title = None
        
        # Choose appropriate columns based on method and parameters
        if method == 'tsne' and tsne_perplexity is not None:
            # 2D t-SNE
            x_col_2d = f'p{tsne_perplexity}_x'
            y_col_2d = f'p{tsne_perplexity}_y'
            df_2d = tsne_2d_df
            
            # 3D t-SNE
            x_col_3d = f'p{tsne_perplexity}_x'
            y_col_3d = f'p{tsne_perplexity}_y'
            z_col_3d = f'p{tsne_perplexity}_z'
            df_3d = tsne_3d_df
            
            title_suffix = f" (perplexity={tsne_perplexity})"
            
        elif method == 'umap' and umap_n_neighbor is not None and umap_min_dist_val is not None:
            # 2D UMAP
            x_col_2d = f'n{umap_n_neighbor}_d{umap_min_dist_val:.1f}_x'
            y_col_2d = f'n{umap_n_neighbor}_d{umap_min_dist_val:.1f}_y'
            df_2d = umap_2d_df
            
            # 3D UMAP
            x_col_3d = f'n{umap_n_neighbor}_d{umap_min_dist_val:.1f}_x'
            y_col_3d = f'n{umap_n_neighbor}_d{umap_min_dist_val:.1f}_y'
            z_col_3d = f'n{umap_n_neighbor}_d{umap_min_dist_val:.1f}_z'
            df_3d = umap_3d_df
            
            title_suffix = f" (n_neighbors={umap_n_neighbor}, min_dist={umap_min_dist_val})"
            
        elif method == 'pca':
            # 2D PCA
            x_col_2d = 'pca_2d_x'
            y_col_2d = 'pca_2d_y'
            df_2d = pca_df
            
            # 3D PCA
            x_col_3d = 'pca_3d_x'
            y_col_3d = 'pca_3d_y'
            z_col_3d = 'pca_3d_z'
            df_3d = pca_df
            
            title_suffix = ""
            
        else:
            return go.Figure()  # Return empty figure if parameters are invalid
        
        # Check if the columns exist in the dataframes
        has_2d = df_2d is not None and not df_2d.empty and x_col_2d in df_2d.columns and y_col_2d in df_2d.columns
        has_3d = df_3d is not None and not df_3d.empty and x_col_3d in df_3d.columns and y_col_3d in df_3d.columns and z_col_3d in df_3d.columns
        
        # Add 2D scatter plot
        if has_2d:
            # Create a scatter plot for 2D
            text_column = color_column  # Use the same column for hover text
            hover_text = base_df[text_column] if text_column else None
            
            # Prepare custom data for click/hover details
            custom_data = base_df['clean_text'] if 'clean_text' in base_df.columns else None
            
            # Create the 2D scatter plot
            scatter_2d = go.Scatter(
                x=df_2d[x_col_2d],
                y=df_2d[y_col_2d],
                mode='markers',
                marker=dict(
                    size=8,
                    color=color_values,  # Using numeric indices now
                    colorscale='Viridis',
                    showscale=True if color_values is not None else False,
                    colorbar=dict(title=color_title) if color_title else dict(),
                    opacity=0.8
                ),
                text=hover_text,
                customdata=custom_data,
                hovertemplate="<b>%{text}</b><br><br>Click for details",
                showlegend=False
            )
            fig.add_trace(scatter_2d, row=1, col=1)
        
        # Add 3D scatter plot
        if has_3d:
            # Create a scatter plot for 3D
            text_column = color_column  # Use the same column for hover text
            hover_text = base_df[text_column] if text_column else None
            
            # Prepare custom data for click/hover details
            custom_data = base_df['clean_text'] if 'clean_text' in base_df.columns else None
            
            # Create the 3D scatter plot
            scatter_3d = go.Scatter3d(
                x=df_3d[x_col_3d],
                y=df_3d[y_col_3d],
                z=df_3d[z_col_3d],
                mode='markers',
                marker=dict(
                    size=5,
                    color=color_values,  # Using numeric indices now
                    colorscale='Viridis',
                    showscale=True if color_values is not None else False,
                    colorbar=dict(title=color_title) if color_title else dict(),
                    opacity=0.8
                ),
                text=hover_text,
                customdata=custom_data,
                hovertemplate="<b>%{text}</b><br><br>Click for details",
                showlegend=False
            )
            fig.add_trace(scatter_3d, row=1, col=2)
        
        # Update layout
        fig.update_layout(
            title=f"{method.upper()} Embeddings{title_suffix}",
            height=800,
            dragmode='select',
            clickmode='event+select',
            hovermode='closest'
        )
        
        # Update 2D subplot axes
        if has_2d:
            fig.update_xaxes(title=f"Dimension 1", row=1, col=1)
            fig.update_yaxes(title=f"Dimension 2", row=1, col=1)
        
        # Update 3D subplot axes
        if has_3d:
            fig.update_scenes(
                xaxis_title=f"Dimension 1",
                yaxis_title=f"Dimension 2",
                zaxis_title=f"Dimension 3"
            )
        
        return fig





    @app.callback(
        Output('hover-data', 'children'),
        [Input('visualization-plot', 'clickData')]
    )
    def display_click_data(clickData):
        if clickData is None:
            return "Click on a point to see details here."
        
        point_data = clickData['points'][0]
        if 'customdata' in point_data:
            content_type = point_data['text']
            text_contents = point_data['customdata']
            
            return html.Div([
                html.H4(f"Content Type: {content_type}"),
                html.Pre(text_contents[:500] + "..." if len(text_contents) > 500 else text_contents)
            ])
        else:
            return "No customdata available for this point."
    
    return app


if __name__ == "__main__":
    import sys
    from pathlib import Path
    import pandas as pd
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Ask for the embeddings file
    data_folder = r'C:\Users\jonma\Sync\skellybot-data\H_M_N_2_5_data'
    base_name = Path(data_folder).stem.replace('_data', '')
    
    # Load the embeddings dataframes
    embedding_dfs = {}
    for df_type in ['base', 'tsne_2d', 'tsne_3d', 'umap_2d', 'umap_3d', 'pca']:
        df_path = Path(data_folder) / f"{base_name}_embeddings_{df_type}.csv"
        if df_path.exists():
            embedding_dfs[df_type] = pd.read_csv(df_path)
            logger.info(f"Loaded {df_type} dataframe with {len(embedding_dfs[df_type])} rows")
    
    if not embedding_dfs:
        logger.error("No embedding dataframes found!")
        sys.exit(1)
    
    # Setup output path for HTML
    html_file_path = Path(data_folder) / f"{base_name}_embeddings_visualization.html"
    
    # Create and run the Dash app
    app = create_dash_app(embedding_dfs, embedding_dfs['base'], save_html_path=str(html_file_path))
    logger.info(f"Running Dash app server...")
    app.run_server(debug=True, port=8050)
    logger.info(f"Dash app server stopped.")