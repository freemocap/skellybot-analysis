import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from scripts.load_csvs import cumulative_counts_df, augmented_users_df, human_messages_df, augmented_messages_df, \
    ai_thread_analysis_df, embedding_projections_tsne_3d_df, embedding_projections_tsne_2d_df
from skellybot_analysis import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def initialize_figure():
    logger.info("Initializing figure")
    fig = make_subplots(
        rows=2, cols=5,
        specs=[[{"colspan": 3}, None, None, {"colspan": 2}, None],  # Mark 4th column as 3D scene
               [{}, {}, {}, {}, {}]],
        subplot_titles=("", "", "", "", "", "", "", "", "", ""),  # Optional: Add titles if needed
    )
    fig.update_layout(
        height=800,
        width=1200,
        title_text="Skellybot Analysis",
        title_x=0.5,
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(size=12),
    )
    return fig


# Helper function for histogram subplots with common elements
def _add_histogram_with_stats(fig: go.Figure, data: pd.Series,
                              subplot_row: int, subplot_col: int,
                              x_title: str, color: str, max_bin: float = None):
    # Calculate statistics
    mean_val = data.mean()
    median_val = data.median()
    hist_bins = max_bin if max_bin else data.max()
    max_freq = np.histogram(data, bins=30, range=(0, hist_bins))[0].max()
    logger.info(
        f"Creating histogram for {x_title} (row {subplot_row}, col {subplot_col}), data size: {len(data)}, max_freq: {max_freq}, mean: {mean_val}, median: {median_val}, max_bin: {max_bin}, hist_bins: {hist_bins}")

    # Add histogram trace
    fig.add_trace(go.Histogram(
        x=data,
        nbinsx=30,
        marker_color=color,
        name=x_title
    ), row=subplot_row, col=subplot_col)

    # Add statistical lines and annotations

    for val, color, text, y_pos in [
        (mean_val, "red", f"Mean: {mean_val:.1f}", 0.9),
        (median_val, "green", f"Median: {median_val:.1f}", 0.75)
    ]:
        fig.add_vline(
            x=val, line_dash="dash", line_color=color,
            row=subplot_row, col=subplot_col
        )
        fig.add_annotation(
            x=val, y=max_freq * y_pos,
            text=text, showarrow=True,
            arrowhead=2, font=dict(color=color),
            row=subplot_row, col=subplot_col
        )

    # Axis labels
    fig.update_xaxes(title_text=x_title, row=subplot_row, col=subplot_col)
    fig.update_yaxes(title_text="Frequency", row=subplot_row, col=subplot_col)


def create_embedding_subplot(fig: go.Figure,
                             tsne2d_df: pd.DataFrame,
                             subplot_row: int,
                             subplot_col: int):
    """Create 3D t-SNE embedding visualization colored by user"""

    fig.add_trace(
        go.Scatter(
            x=tsne2d_df['p30_x'],
            y=tsne2d_df['p30_y'],
            mode='markers',
            marker=dict(
                size=5,
                color=tsne2d_df['id'],  # Color by entity ID (thread, user, or message)
            ),
        ),
        row=subplot_row, col=subplot_col
    )

    # Set 3D scene properties
    fig.update_scenes(
        xaxis_title='Dimension 1',
        yaxis_title='Dimension 2',
        zaxis_title='Dimension 3',
        row=subplot_row, col=subplot_col
    )

    # Histogram subplot functions using helper



def create_cumulative_message_count_plot(fig: go.Figure,
                                         cumulative_counts_df: pd.DataFrame,
                                         subplot_row: int,
                                         subplot_col: int):
    # Add traces for the cumulative message count
    logger.info(
        f"Creating cumulative message count plot for {len(cumulative_counts_df['author_id'].unique())} users (row {subplot_row}, col {subplot_col})")
    for user_id in cumulative_counts_df['author_id'].unique():
        user_data = cumulative_counts_df[cumulative_counts_df['author_id'] == user_id]
        fig.add_trace(
            go.Scatter(
                x=user_data['timestamp'],
                y=user_data['cumulative_message_count'],
                mode='lines+markers',
                name=f'User {user_id}',
                line=dict(width=3),
                marker=dict(size=6)
            ),
            row=subplot_row, col=subplot_col
        )


def create_subplots(fig: go.Figure):

    create_cumulative_message_count_plot(fig=fig,
                                         cumulative_counts_df=cumulative_counts_df,
                                         subplot_row=1,
                                         subplot_col=1)

    create_embedding_subplot(fig=fig,
                             tsne2d_df=embedding_projections_tsne_2d_df,
                             subplot_row=1,
                             subplot_col=4
                             )

    _add_histogram_with_stats(
        fig=fig,
        data=augmented_users_df['total_messages_sent'],
        subplot_row=2,
        subplot_col=1,
        x_title='Messages per User',
        color='#19D3F3'
    )

    # create_threads_per_user_histogram_subplot
    _add_histogram_with_stats(
        fig=fig,
        data=augmented_users_df['threads_participated'],
        subplot_row=2,
        subplot_col=2,
        x_title='Threads per User',
        color='#FFA15A'
    )

    # create_words_per_user_histogram_subplot
    _add_histogram_with_stats(
        fig=fig,
        data=augmented_users_df['total_words_sent'],
        subplot_row=2,
        subplot_col=3,
        x_title='Words per User',
        color='#FF6692'
    )

    # create_messages_per_thread_histogram_subplot
    _add_histogram_with_stats(
        fig=fig,
        data=human_messages_df.groupby('thread_id').size(),
        subplot_row=2,
        subplot_col=4,
        x_title='Human Messages per Thread',
        color='#636EFA'
    )

    # create_words_per_message_histogram_subplot
    _add_histogram_with_stats(
        fig=fig,
        data=human_messages_df['human_word_count'],
        subplot_row=2,
        subplot_col=5,
        x_title='Words per Message',
        color='#B6E880',
        max_bin=300
    )


def viz_main():
    fig = initialize_figure()
    create_subplots(fig=fig)
    
    # Add explicit renderer configuration
    fig.show(renderer="browser")  # Force browser rendering
    
    # Add cleanup for potential hanging processes
    import plotly.io as pio
    pio.kaleido.scope._shutdown_kaleido()  # Cleanup any remaining rendering processes


if __name__ == "__main__":
    viz_main()
