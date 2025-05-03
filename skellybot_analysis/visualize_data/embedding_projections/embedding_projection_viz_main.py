import logging
from pathlib import Path
import functools
from flask_caching import Cache
import time

import dash
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html, Input, Output, State, callback_context
from plotly.subplots import make_subplots

from scripts.load_csvs import embedding_projections_tsne_2d_df, embedding_projections_tsne_3d_df, \
    embedding_projections_umap_3d_df, embedding_projections_pca_df, embedding_projections_umap_2d_df
from skellybot_analysis.data_models.analysis_models import AiThreadAnalysisModel
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

logger = logging.getLogger(__name__)

# Global cache for expensive computations
GLOBAL_CACHE = {}

# Create a more aggressive cache configuration
def create_cache(app):
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 3600,  # 1 hour - much longer timeout
        'CACHE_THRESHOLD': 1000  # Store up to 1000 items in the cache
    })
    return cache

# Precompute all possible figures and store them in memory
def precompute_figures(processed_dfs, projection_types, param_versions):
    """Precompute all possible figures for faster access."""
    figures = {}
    thread_connections_data = {}
    
    # Define marker symbols for different content types
    marker_symbols = {
        'message_and_response': 'circle',
        'thread_analysis': 'diamond'
    }
    
    # Precompute thread color maps
    thread_color_maps = {}
    
    for proj_type in projection_types:
        df_2d = processed_dfs[f"{proj_type}_2d"]
        df_3d = processed_dfs.get(f"{proj_type}_3d", processed_dfs.get(f"{proj_type}", None))
        
        # Generate thread color map once per projection type
        thread_ids = pd.concat([
            df_2d[['thread_id']].dropna(),
            df_3d[['thread_id']].dropna() if df_3d is not None else pd.DataFrame()
        ]).drop_duplicates()['thread_id'].tolist()
        
        thread_colors = px.colors.qualitative.Plotly + px.colors.qualitative.D3 + px.colors.qualitative.G10
        thread_color_map = {
            str(thread_id): thread_colors[i % len(thread_colors)]
            for i, thread_id in enumerate(thread_ids)
        }
        thread_color_maps[proj_type] = thread_color_map
        
        # Precompute figures for each parameter version and content filter
        for param_version in param_versions.get(proj_type, []):
            for content_filter in ['all', 'message_and_response', 'thread_analysis']:
                # Filter data
                df_2d_filtered = df_2d.copy()
                df_3d_filtered = df_3d.copy() if df_3d is not None else None
                
                if content_filter != 'all':
                    df_2d_filtered = df_2d_filtered[df_2d_filtered['content_type'] == content_filter]
                    if df_3d_filtered is not None:
                        df_3d_filtered = df_3d_filtered[df_3d_filtered['content_type'] == content_filter]
                
                # Create figure
                fig = make_subplots(
                    rows=1, cols=2,
                    specs=[[{'type': 'xy'}, {'type': 'scene'}]],
                    subplot_titles=('2D Projection', '3D Projection')
                )
                
                # Add 2D scatter plot
                x_col, y_col = get_projection_columns(proj_type, param_version, dim=2)
                add_2d_trace(fig, df_2d_filtered, x_col, y_col, thread_color_map, marker_symbols)
                
                # Add 3D scatter plot if available
                if df_3d_filtered is not None and not df_3d_filtered.empty:
                    x_col_3d, y_col_3d, z_col_3d = get_projection_columns(proj_type, param_version, dim=3)
                    add_3d_trace(fig, df_3d_filtered, x_col_3d, y_col_3d, z_col_3d, thread_color_map, marker_symbols)
                
                # Update layout
                fig.update_layout(
                    title=f"{proj_type.upper()} Projections - {param_version}",
                    showlegend=True,
                    legend_title_text='Content Type',
                    hovermode='closest'
                )
                
                # Update axis labels
                update_axis_labels(fig, proj_type)
                
                # Store figure
                key = f"{proj_type}_{param_version}_{content_filter}"
                figures[key] = fig
                
                # Precompute thread connections data
                thread_connections = {}
                if 'thread_id' in df_2d_filtered.columns:
                    for thread_id in df_2d_filtered['thread_id'].unique():
                        if pd.notna(thread_id):
                            thread_points = df_2d_filtered[df_2d_filtered['thread_id'] == thread_id]
                            if not thread_points.empty and len(thread_points) > 1:
                                thread_connections[str(thread_id)] = {
                                    'x': thread_points[x_col].tolist(),
                                    'y': thread_points[y_col].tolist(),
                                    'ids': thread_points['id'].tolist()
                                }
                
                thread_connections_data[key] = thread_connections
    
    return figures, thread_connections_data, thread_color_maps

def get_projection_columns(projection_type: str, param_version: str, dim: int = 2) -> tuple:
    """Get the appropriate column names for the projection type and parameters."""
    cache_key = f"proj_cols_{projection_type}_{param_version}_{dim}"
    if cache_key in GLOBAL_CACHE:
        return GLOBAL_CACHE[cache_key]
    
    if projection_type == 'tsne':
        # For t-SNE, param_version is the perplexity value (e.g., 'p5', 'p10', etc.)
        if dim == 2:
            result = f'{param_version}_x', f'{param_version}_y'
        else:  # dim == 3
            result = f'{param_version}_x', f'{param_version}_y', f'{param_version}_z'
    elif projection_type == 'umap':
        # For UMAP, param_version is like 'n15_d0.1' (n_neighbors and min_dist)
        if dim == 2:
            result = f'{param_version}_x', f'{param_version}_y'
        else:  # dim == 3
            result = f'{param_version}_x', f'{param_version}_y', f'{param_version}_z'
    elif projection_type == 'pca':
        # For PCA, we use fixed column names
        if dim == 2:
            result = 'pca_3d_x', 'pca_3d_y'
        else:  # dim == 3
            result = 'pca_3d_x', 'pca_3d_y', 'pca_3d_z'
    else:
        raise ValueError(f"Unknown projection type: {projection_type}")
    
    GLOBAL_CACHE[cache_key] = result
    return result


def update_axis_labels(fig: go.Figure, projection_type: str):
    """Update axis labels based on the projection type."""
    # 2D plot axis labels
    fig.update_xaxes(title=f"{projection_type.upper()} Dimension 1", row=1, col=1)
    fig.update_yaxes(title=f"{projection_type.upper()} Dimension 2", row=1, col=1)

    # 3D plot axis labels
    fig.update_scenes(
        xaxis_title=f"{projection_type.upper()} Dimension 1",
        yaxis_title=f"{projection_type.upper()} Dimension 2",
        zaxis_title=f"{projection_type.upper()} Dimension 3"
    )


def create_projection_explorer_app(projection_dfs: dict[str, pd.DataFrame]) -> dash.Dash:
    """Create a Dash app for exploring embedding projections."""
    start_time = time.time()
    logger.info("Starting app creation...")
    
    app = dash.Dash(__name__)
    cache = create_cache(app)
    
    # Process dataframes once at startup
    def preprocess_dataframes(dfs):
        logger.info("Preprocessing dataframes...")
        processed_dfs = {}
        for df_name, df in dfs.items():
            processed_df = df.copy()
            if 'thread_id' not in processed_df.columns:
                # For message_and_response, extract thread_id from the human_messages_df
                mask_msg = processed_df['content_type'] == 'message_and_response'
                if any(mask_msg):
                    # Try to load thread_id from human_messages.csv
                    try:
                        db_path = Path(get_most_recent_db_location())
                        messages_df = pd.read_csv(db_path / 'human_messages.csv')
                        id_to_thread = messages_df.set_index('message_id')['thread_id'].to_dict()

                        # Create a new thread_id column
                        processed_df['thread_id'] = None
                        # For message_and_response, use the thread_id from human_messages
                        processed_df.loc[mask_msg, 'thread_id'] = processed_df.loc[mask_msg, 'id'].map(id_to_thread)
                        # For thread_analysis, the id is already the thread_id
                        processed_df.loc[processed_df['content_type'] == 'thread_analysis', 'thread_id'] = processed_df.loc[processed_df['content_type'] == 'thread_analysis', 'id']
                    except Exception as e:
                        logger.error(f"Failed to add thread_id to dataframe: {e}")
            processed_dfs[df_name] = processed_df
        return processed_dfs
    
    # Process dataframes once
    processed_projection_dfs = preprocess_dataframes(projection_dfs)
    logger.info(f"Dataframes preprocessed in {time.time() - start_time:.2f} seconds")

    # Extract available projection types from the dataframe keys
    projection_types = [pt for pt in ['tsne', 'umap', 'pca'] if f"{pt}_2d" in processed_projection_dfs or f"{pt}_3d" in processed_projection_dfs or f"{pt}" in processed_projection_dfs]

    # Get parameter versions for each projection type
    def get_param_versions(proj_dfs):
        logger.info("Getting parameter versions...")
        param_versions = {}
        for proj_type in projection_types:
            if f"{proj_type}_2d" in proj_dfs:
                df = proj_dfs[f"{proj_type}_2d"]
                # Extract parameter versions from column names
                if proj_type == 'tsne':
                    # For t-SNE, columns are like 'p5_x', 'p5_y', etc.
                    param_versions[proj_type] = sorted([col.split('_')[0] for col in df.columns if col.endswith('_x')])
                elif proj_type == 'umap':
                    # For UMAP, columns are like 'n5_d0.1_x', 'n5_d0.1_y', etc.
                    param_versions[proj_type] = sorted([col.split('_x')[0] for col in df.columns if col.endswith('_x')])
                elif proj_type == 'pca':
                    # For PCA, we just have one version
                    param_versions[proj_type] = ['pca_3d']
        return param_versions
    
    param_versions = get_param_versions(processed_projection_dfs)
    logger.info(f"Parameter versions extracted in {time.time() - start_time:.2f} seconds")
    
    # Precompute all figures
    logger.info("Precomputing figures...")
    precomputed_figures, thread_connections_data, thread_color_maps = precompute_figures(
        processed_projection_dfs, projection_types, param_versions
    )
    logger.info(f"Figures precomputed in {time.time() - start_time:.2f} seconds")
    
    # Create a lookup dictionary for point details
    point_details_lookup = {}
    for proj_type in projection_types:
        df = processed_projection_dfs[f"{proj_type}_2d"]
        for _, row in df.iterrows():
            point_id = row['id']
            point_details_lookup[point_id] = {
                'id': point_id,
                'content_type': row['content_type'],
                'thread_id': row.get('thread_id', None),
                'text': row.get('text', '')
            }
    logger.info(f"Point details lookup created in {time.time() - start_time:.2f} seconds")

    app.layout = html.Div([
        html.H1("Embedding Projections Explorer"),

        html.Div([
            html.Div([
                html.Label("Projection Type:"),
                dcc.Dropdown(
                    id='projection-type',
                    options=[{'label': pt.upper(), 'value': pt} for pt in projection_types],
                    value=projection_types[0] if projection_types else None
                ),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

            html.Div([
                html.Label("Parameter Version:"),
                dcc.Dropdown(
                    id='parameter-version',
                    # Options will be set by callback
                ),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

            html.Div([
                html.Label("Content Filter:"),
                dcc.Dropdown(
                    id='content-filter',
                    options=[
                        {'label': 'All', 'value': 'all'},
                        {'label': 'Messages & Responses', 'value': 'message_and_response'},
                        {'label': 'Thread Analyses', 'value': 'thread_analysis'}
                    ],
                    value='all'
                ),
            ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        ]),

        html.Div([
            dcc.Graph(
                id='projection-plot',
                style={'height': '80vh'},
                config={'displayModeBar': True}
            ),
        ]),

        # Store components for sharing data between callbacks
        dcc.Store(id='hovered-point-data'),
        dcc.Store(id='current-figure-key', data=""),

        # Point details panel
        html.Div([
            html.H3("Point Details"),
            html.Div(id='point-details')
        ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'marginTop': '20px'})
    ])

    @app.callback(
        Output('parameter-version', 'options'),
        Output('parameter-version', 'value'),
        Input('projection-type', 'value')
    )
    def update_param_versions(projection_type):
        """Update parameter version options based on selected projection type."""
        if not projection_type or projection_type not in param_versions:
            return [], None

        options = [{'label': pv, 'value': pv} for pv in param_versions[projection_type]]
        default_value = param_versions[projection_type][0] if param_versions[projection_type] else None

        return options, default_value

    @app.callback(
        Output('current-figure-key', 'data'),
        [Input('projection-type', 'value'),
         Input('parameter-version', 'value'),
         Input('content-filter', 'value')]
    )
    def update_figure_key(projection_type, param_version, content_filter):
        """Update the current figure key based on selections."""
        if not projection_type or not param_version:
            return ""
        return f"{projection_type}_{param_version}_{content_filter}"

    @app.callback(
        Output('hovered-point-data', 'data'),
        Input('projection-plot', 'hoverData')
    )
    def store_hovered_point(hover_data):
        """Store data about the currently hovered point."""
        if not hover_data:
            return None

        # Extract point data from hover event
        point_data = hover_data['points'][0]

        # Check if customdata is available (contains id, content_type, thread_id)
        if 'customdata' in point_data:
            return {
                'id': point_data['customdata'][0],
                'content_type': point_data['customdata'][1],
                'thread_id': point_data['customdata'][2]
            }
        return None

    @app.callback(
        Output('point-details', 'children'),
        Input('projection-plot', 'clickData')
    )
    def display_point_details(click_data):
        """Display details about the clicked point."""
        if not click_data:
            return "Click on a point to see details"

        point_data = click_data['points'][0]

        # Check if customdata is available
        if 'customdata' not in point_data:
            return "No detailed information available for this point"

        point_id = point_data['customdata'][0]
        
        # Get point details from lookup
        if point_id not in point_details_lookup:
            return "Point information not found"
        
        point_info = point_details_lookup[point_id]
        
        # Create details display
        details = []
        details.append(html.H4(f"ID: {point_id}"))
        details.append(html.P(f"Content Type: {point_info['content_type']}"))

        if point_info['thread_id'] and pd.notna(point_info['thread_id']):
            details.append(html.P(f"Thread ID: {point_info['thread_id']}"))

        # Add text preview if available
        if 'text' in point_info and point_info['text']:
            text = point_info['text']
            # Truncate text if it's too long
            preview = text[:500] + "..." if len(text) > 500 else text
            details.append(html.H5("Text Preview:"))
            details.append(html.Div(
                preview,
                style={'whiteSpace': 'pre-wrap', 'backgroundColor': '#eee', 'padding': '10px', 'borderRadius': '5px'}
            ))

        return details

    @app.callback(
        Output('projection-plot', 'figure'),
        [Input('current-figure-key', 'data'),
         Input('hovered-point-data', 'data')]
    )
    def update_projections(figure_key: str, hovered_point_data):
        """Update the plots based on user selections and hover state."""
        if not figure_key or figure_key not in precomputed_figures:
            # Return empty figure if no valid key
            return go.Figure()

        # Get the precomputed figure
        fig = precomputed_figures[figure_key].copy()
        
        # If a point is hovered, add connections for its thread
        if hovered_point_data and 'thread_id' in hovered_point_data:
            thread_id = hovered_point_data['thread_id']
            if thread_id and str(thread_id) in thread_connections_data[figure_key]:
                conn_data = thread_connections_data[figure_key][str(thread_id)]
                
                # Add a line connecting all points in this thread
                fig.add_trace(
                    go.Scatter(
                        x=conn_data['x'],
                        y=conn_data['y'],
                        mode='lines',
                        line=dict(color='rgba(0,0,0,0.7)', width=2),
                        showlegend=False,
                        hoverinfo='none'
                    ),
                    row=1, col=1
                )
                
                # Extract projection type from figure key
                projection_type = figure_key.split('_')[0]
                param_version = figure_key.split('_')[1]
                content_filter = figure_key.split('_')[2]
                
                # Get the dataframe for highlighting
                df_2d = processed_projection_dfs[f"{projection_type}_2d"]
                if content_filter != 'all':
                    df_2d = df_2d[df_2d['content_type'] == content_filter]
                
                # Get column names
                x_col, y_col = get_projection_columns(projection_type, param_version, dim=2)
                
                # Highlight the points in this thread
                thread_points = df_2d[df_2d['thread_id'] == thread_id]
                for content_type in thread_points['content_type'].unique():
                    mask = (thread_points['content_type'] == content_type)
                    fig.add_trace(
                        go.Scatter(
                            x=thread_points.loc[mask, x_col],
                            y=thread_points.loc[mask, y_col],
                            mode='markers',
                            marker=dict(
                                color=thread_color_maps[projection_type].get(str(thread_id), '#000000'),
                                symbol='circle' if content_type == 'message_and_response' else 'diamond',
                                size=12,
                                line=dict(color='black', width=2)
                            ),
                            showlegend=False,
                            hoverinfo='none'
                        ),
                        row=1, col=1
                    )

        return fig

    
    logger.info(f"App creation completed in {time.time() - start_time:.2f} seconds")
    return app

def add_2d_trace(fig: go.Figure, df: pd.DataFrame, x_col: str, y_col: str, 
                    thread_color_map: dict, marker_symbols: dict):
    """Add 2D scatter trace to figure with thread-based coloring and content-type symbols."""
    # Group by content type first
    for content_type, symbol in marker_symbols.items():
        content_mask = df['content_type'] == content_type
        
        # Create a trace for each thread within this content type
        for thread_id in df.loc[content_mask, 'thread_id'].dropna().unique():
            thread_mask = (content_mask) & (df['thread_id'] == thread_id)
            
            # Skip if no points match
            if not any(thread_mask):
                continue
            
            # Get color for this thread
            color = thread_color_map.get(str(thread_id), '#000000')
            
            # Create name for legend that combines content type and thread
            legend_name = f"{content_type} (Thread {thread_id})"
            
            # Add trace for this thread and content type
            fig.add_trace(
                go.Scatter(
                    x=df.loc[thread_mask, x_col],
                    y=df.loc[thread_mask, y_col],
                    mode='markers',
                    marker=dict(
                        color=color,
                        symbol=symbol,
                        size=8,
                        opacity=0.7
                    ),
                    name=legend_name,
                    text=df.loc[thread_mask, 'id'],
                    customdata=df.loc[thread_mask, ['id', 'content_type', 'thread_id']].values,
                    hovertemplate="<b>%{text}</b><br>"
                                f"Thread: %{{customdata[2]}}<br>"
                                f"X: %{{x:.2f}}<br>Y: %{{y:.2f}}<extra>{content_type}</extra>"
                ),
                row=1, col=1
            )

def add_3d_trace(fig: go.Figure, df: pd.DataFrame,
                    x_col: str, y_col: str, z_col: str,
                    thread_color_map: dict, marker_symbols: dict):
    """Add 3D scatter trace to figure with thread-based coloring and content-type symbols."""
    # Group by content type first
    for content_type, symbol in marker_symbols.items():
        content_mask = df['content_type'] == content_type
        
        # Create a trace for each thread within this content type
        for thread_id in df.loc[content_mask, 'thread_id'].dropna().unique():
            thread_mask = (content_mask) & (df['thread_id'] == thread_id)
            
            # Skip if no points match
            if not any(thread_mask):
                continue
            
            # Get color for this thread
            color = thread_color_map.get(str(thread_id), '#000000')
            
            # Create name for legend that combines content type and thread
            legend_name = f"{content_type} (Thread {thread_id})"
            
            # Add trace for this thread and content type
            fig.add_trace(
                go.Scatter3d(
                    x=df.loc[thread_mask, x_col],
                    y=df.loc[thread_mask, y_col],
                    z=df.loc[thread_mask, z_col],
                    mode='markers',
                    marker=dict(
                        color=color,
                        symbol=symbol,
                        size=5,
                        opacity=0.7
                    ),
                    name=legend_name,
                    text=df.loc[thread_mask, 'id'],
                    customdata=df.loc[thread_mask, ['id', 'content_type', 'thread_id']].values,
                    hovertemplate="<b>%{text}</b><br>"
                                f"Thread: %{{customdata[2]}}<br>"
                                f"X: %{{x:.2f}}<br>Y: %{{y:.2f}}<br>Z: %{{z:.2f}}<extra>{content_type}</extra>"
                ),
                row=1, col=2
            )
if __name__ == "__main__":
    # Generate and save static versions of the visualization
    logger.info("Generating static visualization files")
    _db_directory = Path(get_most_recent_db_location())
    _db_name = _db_directory.stem.replace("_data", "")
    visualization_name = f"{_db_name}_skellybot_visualization"

    # Create and run the projection explorer
    proj_app = create_projection_explorer_app({
        'tsne_2d': embedding_projections_tsne_2d_df,
        'tsne_3d': embedding_projections_tsne_3d_df,
        'umap_2d': embedding_projections_umap_2d_df,
        'umap_3d': embedding_projections_umap_3d_df,
        'pca_2d': embedding_projections_pca_df, # PCA is the same for 3d and 2d, so we dummy it to match the pattern
        'pca_3d': embedding_projections_pca_df
    })
     
    proj_app.run_server(port=8051, debug=False)  # Disable debug mode for better performance