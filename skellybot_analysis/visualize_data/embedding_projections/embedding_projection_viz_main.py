import logging
from pathlib import Path

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import html, Input, Output
from plotly.subplots import make_subplots

from scripts.load_csvs import embedding_projections_tsne_2d_df, embedding_projections_tsne_3d_df, \
    embedding_projections_umap_3d_df, embedding_projections_pca_df, embedding_projections_umap_2d_df
from skellybot_analysis import configure_logging
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

configure_logging()
logger = logging.getLogger(__name__)



def create_projection_explorer_app(projection_dfs: dict[str, pd.DataFrame]) -> dash.Dash:
    """Create a Dash app for exploring embedding projections."""
    app = dash.Dash(__name__)

    # Extract available projection types from the dataframe keys
    projection_types = [pt for pt in ['tsne', 'umap', 'pca'] if f"{pt}_2d" in projection_dfs or f"{pt}_3d" in projection_dfs or f"{pt}" in projection_dfs]

    # Add thread_id to all dataframes if not already present
    for df_name, df in projection_dfs.items():
        if 'thread_id' not in df.columns:
            # For message_and_response, extract thread_id from the human_messages_df
            mask_msg = df['content_type'] == 'message_and_response'
            if any(mask_msg):
                # Try to load thread_id from human_messages.csv
                try:
                    db_path = Path(get_most_recent_db_location())
                    messages_df = pd.read_csv(db_path / 'human_messages.csv')
                    id_to_thread = messages_df.set_index('message_id')['thread_id'].to_dict()
                    
                    # Create a new thread_id column
                    df['thread_id'] = None
                    # For message_and_response, use the thread_id from human_messages
                    df.loc[mask_msg, 'thread_id'] = df.loc[mask_msg, 'id'].map(id_to_thread)
                    # For thread_analysis, the id is already the thread_id
                    df.loc[df['content_type'] == 'thread_analysis', 'thread_id'] = df.loc[df['content_type'] == 'thread_analysis', 'id']
                except Exception as e:
                    logger.error(f"Failed to add thread_id to dataframe: {e}")

    app.layout = html.Div([
        # ... rest of layout code here ...
    ])

    # ... rest of code here ...

    @app.callback(
        [Output('projection-plot', 'figure'),
         Output('thread-connections-data', 'data')],
        [Input('projection-type', 'value'),
         Input('parameter-version', 'value'),
         Input('hovered-point-data', 'data')]
    )
    def update_projections(projection_type: str, param_version: str, hovered_point_data):
        """Update the plots based on user selections and hover state."""
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{'type': 'xy'}, {'type': 'scene'}]],
            subplot_titles=('2D Projection', '3D Projection')
        )

        # Get dataframes
        df_2d = projection_dfs[f"{projection_type}_2d"]
        df_3d = projection_dfs[f"{projection_type}_3d"]

        # Generate a color map based on unique thread IDs
        thread_ids = pd.concat([
            df_2d[['thread_id']].dropna(),
            df_3d[['thread_id']].dropna()
        ]).drop_duplicates()['thread_id'].tolist()
        
        # Create a colorscale for threads
        import plotly.express as px
        thread_colors = px.colors.qualitative.Plotly + px.colors.qualitative.D3 + px.colors.qualitative.G10
        thread_color_map = {
            str(thread_id): thread_colors[i % len(thread_colors)]
            for i, thread_id in enumerate(thread_ids)
        }
        
        # Define marker symbols for different content types
        marker_symbols = {
            'message_and_response': 'circle',
            'thread_analysis': 'diamond'
        }

        # Add 2D scatter plot
        x_col, y_col = get_projection_columns(projection_type, param_version, dim=2)
        add_2d_trace(fig, df_2d, x_col, y_col, thread_color_map, marker_symbols)

        # Add 3D scatter plot if available
        if f"{projection_type}_3d" in projection_dfs:
            x_col_3d, y_col_3d, z_col_3d = get_projection_columns(projection_type, param_version, dim=3)
            add_3d_trace(fig, df_3d, x_col_3d, y_col_3d, z_col_3d, thread_color_map, marker_symbols)

        # Update layout
        fig.update_layout(
            title=f"{projection_type.upper()} Projections - {param_version}",
            showlegend=True,
            legend_title_text='Content Type',
            hovermode='closest'
        )

        # Update axis labels
        update_axis_labels(fig, projection_type)
        
        # Create thread connections data for later use
        thread_connections = {}
        if 'thread_id' in df_2d.columns:
            for thread_id in df_2d['thread_id'].unique():
                if pd.notna(thread_id):
                    thread_points = df_2d[df_2d['thread_id'] == thread_id]
                    if not thread_points.empty and len(thread_points) > 1:
                        thread_connections[str(thread_id)] = {
                            'x': thread_points[x_col].tolist(),
                            'y': thread_points[y_col].tolist(),
                            'ids': thread_points['id'].tolist()
                        }
        
        # If a point is hovered, add connections for its thread
        if hovered_point_data and 'thread_id' in hovered_point_data:
            thread_id = hovered_point_data['thread_id']
            if thread_id and str(thread_id) in thread_connections:
                conn_data = thread_connections[str(thread_id)]
                
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
                                color=thread_color_map.get(str(thread_id), '#000000'),
                                symbol=marker_symbols.get(content_type, 'circle'),
                                size=12,
                                line=dict(color='black', width=2)
                            ),
                            showlegend=False,
                            hoverinfo='none'
                        ),
                        row=1, col=1
                    )

        return fig, thread_connections

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
    r

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

    proj_app.run_server(port=8051)  # Different port from your other app