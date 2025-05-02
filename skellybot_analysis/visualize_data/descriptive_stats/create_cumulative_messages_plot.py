import logging

import pandas as pd
from plotly import graph_objects as go

logger = logging.getLogger(__name__)


def create_cumulative_message_count_by_user(fig: go.Figure,
                                            cumulative_counts_df: pd.DataFrame,
                                            subplot_row: int,
                                            subplot_col: int):
    """Create a plot of cumulative message counts by user"""
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
                line=dict(width=2),
                marker=dict(size=6)
            ),
            row=subplot_row, col=subplot_col
        )

    fig.update_yaxes(title_text="Message Count", row=subplot_row, col=subplot_col)


def create_cumulative_word_count_plot(fig: go.Figure,
                                      cumulative_counts_df: pd.DataFrame,
                                      human_word_color: str,
                                      bot_word_color: str,
                                      subplot_row: int,
                                      subplot_col: int):
    """Create a stacked area plot of cumulative word counts (human and bot)"""
    logger.info(f"Creating cumulative word count stacked area plot (row {subplot_row}, col {subplot_col})")

    # Get the latest timestamp for each metric to get the final counts
    latest_data = cumulative_counts_df.sort_values('timestamp').drop_duplicates(['timestamp'], keep='last')

    # Create lighter versions of the colors for the fill areas
    human_fill_color = _create_lighter_color(human_word_color, alpha=0.25)
    bot_fill_color = _create_lighter_color(bot_word_color, alpha=0.25)

    # Add trace for human word count (bottom layer)
    fig.add_trace(
        go.Scatter(
            x=latest_data['timestamp'],
            y=latest_data['cumulative_human_word_count'],
            mode='lines+markers',
            name='Human Words',
            line=dict(width=2, color=human_word_color),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor=human_fill_color,
        ),
        row=subplot_row, col=subplot_col
    )

    # Add trace for bot word count (stacked on top of human)
    fig.add_trace(
        go.Scatter(
            x=latest_data['timestamp'],
            y=latest_data['cumulative_total_word_count'],  # Total = human + bot
            mode='lines+markers',
            name='Bot Words',
            line=dict(width=2, color=bot_word_color),
            marker=dict(size=6),
            fill='tonexty',  # Fill to the previous trace
            fillcolor=bot_fill_color,
        ),
        row=subplot_row, col=subplot_col
    )

    # Get the midpoint of the time range and the word counts for annotations
    target_index = int(len(latest_data) * .9) + 57

    time_midpoint = latest_data['timestamp'].iloc[target_index]
    human_midpoint = latest_data['cumulative_human_word_count'].iloc[target_index] / 2

    # Calculate the midpoint for bot words (between human total and total)
    bot_midpoint = (latest_data['cumulative_human_word_count'].iloc[target_index] +
                    latest_data['cumulative_total_word_count'].iloc[target_index]) / 2

    # Add annotation for human words area
    fig.add_annotation(
        x=time_midpoint,
        y=human_midpoint,
        text="Human Word Count",
        showarrow=False,
        font=dict(size=20,
                  weight="bold",
                  color=human_word_color),
        row=subplot_row, col=subplot_col
    )

    # Add annotation for bot words area
    fig.add_annotation(
        x=time_midpoint,
        y=bot_midpoint,
        text="Bot Word Count",
        showarrow=False,
        font=dict(size=20,
                  weight="bold",
                  color=bot_word_color),
        row=subplot_row, col=subplot_col
    )

    # Ensure y-axis starts at 0
    fig.update_yaxes(
        title_text="Cumulative Word Count",
        range=[0, latest_data['cumulative_total_word_count'].max() * 1.05],  # Add 5% padding at top
        row=subplot_row,
        col=subplot_col
    )

    fig.update_xaxes(title_text="Date", row=subplot_row, col=subplot_col)


def _create_lighter_color(color: str, alpha: float = 0.5) -> str:
    """Create a lighter/transparent version of a color for fill areas"""
    # Handle hex colors
    if color.startswith('#'):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        return f"rgba({r},{g},{b},{alpha})"

    # Handle rgb colors
    elif color.startswith('rgb('):
        rgb_values = color.strip('rgb()').split(',')
        r, g, b = [int(val.strip()) for val in rgb_values]
        return f"rgba({r},{g},{b},{alpha})"

    # Handle rgba colors
    elif color.startswith('rgba('):
        rgba_values = color.strip('rgba()').split(',')
        r, g, b = [int(val.strip()) for val in rgba_values[:3]]
        return f"rgba({r},{g},{b},{alpha})"

    # Return original color if format is unknown
    return color
