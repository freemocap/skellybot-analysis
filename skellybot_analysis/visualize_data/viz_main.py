import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from skellybot_analysis.visualize_data.load_dataframes import load_dataframes


def initialize_figure():
    fig = make_subplots(
        rows=2, cols=5,
        specs=[[{"colspan": 3}, None, None, {"colspan": 2}, None],  # Two double-wide plots on the top row
               [{}, {}, {}, {}, {}]],  # Five single-slot plots on the bottom row
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

    # Add histogram trace
    fig.add_trace(go.Histogram(
        x=data,
        nbinsx=30,
        marker_color=color,
        name=x_title
    ), row=subplot_row, col=subplot_col)

    # Add statistical lines and annotations
    max_freq = np.histogram(data, bins=30, range=(0, hist_bins))[0].max()
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
                             messages_df: pd.DataFrame,
                             analyses_df: pd.DataFrame,
                             tsne3d_df: pd.DataFrame,
                             subplot_row: int,
                             subplot_col: int):
    """Create 3D t-SNE embedding visualization colored by user"""

    # Create 3D scatter for each user
    for user_id in merged_df['author_id'].unique():
        user_df = merged_df[merged_df['author_id'] == user_id]
        fig.add_trace(go.Scatter3d(
            x=user_df['p30_x'],
            y=user_df['p30_y'],
            z=user_df['p30_z'],
            mode='markers',
            name=f'User {user_id}',
            marker=dict(size=3, opacity=0.7)
        ), row=subplot_row, col=subplot_col)

    # Set 3D scene properties
    fig.update_scenes(
        xaxis_title='Dimension 1',
        yaxis_title='Dimension 2',
        zaxis_title='Dimension 3',
        row=subplot_row, col=subplot_col
    )


# Histogram subplot functions using helper
def create_message_per_user_histogram_subplot(fig: go.Figure,
                                              messages_df: pd.DataFrame,
                                              users_df: pd.DataFrame,
                                              subplot_row: int,
                                              subplot_col: int):
    _add_histogram_with_stats(
        fig, users_df['total_messages_sent'],
        subplot_row, subplot_col,
        'Messages per User', '#19D3F3'
    )


def create_threads_per_user_histogram_subplot(fig: go.Figure,
                                              messages_df: pd.DataFrame,
                                              users_df: pd.DataFrame,
                                              threads_df: pd.DataFrame,
                                              subplot_row: int,
                                              subplot_col: int):
    _add_histogram_with_stats(
        fig, users_df['threads_participated'],
        subplot_row, subplot_col,
        'Threads per User', '#FFA15A'
    )


def create_words_per_user_histogram_subplot(fig: go.Figure,
                                            messages_df: pd.DataFrame,
                                            users_df: pd.DataFrame,
                                            subplot_row: int,
                                            subplot_col: int):
    _add_histogram_with_stats(
        fig, users_df['total_words_sent'],
        subplot_row, subplot_col,
        'Words per User', '#FF6692'
    )


def create_messages_per_thread_histogram_subplot(fig: go.Figure,
                                                 messages_df: pd.DataFrame,
                                                 users_df: pd.DataFrame,
                                                 subplot_row: int,
                                                 subplot_col: int):
    thread_counts = messages_df.groupby('thread_id').size()
    _add_histogram_with_stats(
        fig, thread_counts,
        subplot_row, subplot_col,
        'Messages per Thread', '#636EFA'
    )


def create_words_per_message_histogram_subplot(fig: go.Figure,
                                               messages_df: pd.DataFrame,
                                               users_df: pd.DataFrame,
                                               subplot_row: int,
                                               subplot_col: int):
    human_messages = messages_df[messages_df['is_bot'] == False]
    _add_histogram_with_stats(
        fig, human_messages['word_count'],
        subplot_row, subplot_col,
        'Words per Message', '#B6E880', max_bin=300
    )


def create_cumulative_message_count_plot(fig: go.Figure,
                                         cumulative_counts_df: pd.DataFrame,
                                         subplot_row: int,
                                         subplot_col: int):
    # Add traces for the cumulative message count
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


def create_threads_per_user_historgam_subplot(fig: go.Figure,
                                              messages_df: pd.DataFrame,
                                              users_df: pd.DataFrame,
                                              threads_df: pd.DataFrame,
                                              subplot_row: int,
                                              subplot_col: int):
    _add_histogram_with_stats(
        fig, users_df['threads_participated'],
        subplot_row, subplot_col,
        'Threads per User', '#FFA15A'
    )

def create_subplots(fig: go.Figure, data_folder: str):
    (users_df,
     messages_df,
     threads_df,
     cumulative_counts_df,
     analyses_df,
     tsne3d_df) = load_dataframes(data_folder=data_folder)


    create_cumulative_message_count_plot(fig=fig,
                                         cumulative_counts_df=cumulative_counts_df,
                                         subplot_row=1,
                                         subplot_col=1)

    create_embedding_subplot(fig=fig,
                             messages_df=messages_df,
                             analyses_df=analyses_df,
                             tsne3d_df=tsne3d_df,
                             subplot_row=1,
                             subplot_col=2
                             )

    create_message_per_user_histogram_subplot(fig=fig,
                                              messages_df=messages_df,
                                              users_df=users_df,
                                              subplot_row=2,
                                              subplot_col=1
                                              )

    create_threads_per_user_historgam_subplot(fig=fig,
                                              messages_df=messages_df,
                                              users_df=users_df,
                                              threads_df=threads_df,
                                              subplot_row=2,
                                              subplot_col=2
                                              )

    create_words_per_user_histogram_subplot(fig=fig,
                                            messages_df=messages_df,
                                            users_df=users_df,
                                            subplot_row=2,
                                            subplot_col=3
                                            )

    create_messages_per_thread_histogram_subplot(fig=fig,
                                                 messages_df=messages_df,
                                                 users_df=users_df,
                                                 subplot_row=2,
                                                 subplot_col=4
                                                 )

    create_words_per_message_histogram_subplot(fig=fig,
                                               messages_df=messages_df,
                                               users_df=users_df,
                                               subplot_row=2,
                                               subplot_col=4
                                               )




def viz_main(data_folder: str):
    fig = initialize_figure()
    create_subplots(fig=fig, data_folder=data_folder)
    fig.show()


if __name__ == "__main__":
    _data_folder = "C:/Users/jonma/Sync/skellybot-data/H_M_N_2_5_data"
    viz_main(data_folder=_data_folder)
