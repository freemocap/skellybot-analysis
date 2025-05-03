import logging
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc
from dash.dependencies import Input, Output

from scripts.load_csvs import cumulative_counts_df, augmented_users_df, human_messages_df
from skellybot_analysis import configure_logging
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location
from skellybot_analysis.visualize_data.descriptive_stats.create_cumulative_messages_plot import create_cumulative_message_count_by_user, \
    create_cumulative_word_count_plot
from skellybot_analysis.visualize_data.descriptive_stats.create_histogram_subplot import create_histogram_subplot
from plotly.subplots import make_subplots

configure_logging()
logger = logging.getLogger(__name__)


def initialize_figure(db_name: str):
    logger.info("Initializing figure")
    fig = make_subplots(
        rows=2, cols=7,
        specs=[[{"colspan": 3}, None,None, {}, {}, {},{}],
               [{"colspan": 3}, None,None, {"colspan": 2}, None, {"colspan": 2}, None]],
        subplot_titles=(
            "Cumulative Message Count by User",
            "Threads per User",
            "Messages per User",
            "Words per User",
            "Human Messages per Thread",
            "Cumulative Word Count Bot/Human/Total",
            "Words per Human Message",
            "Words per Bot Message",
        ),
        vertical_spacing=0.12,
    )
    fig.update_layout(
        title={
            'text': f"Skellybot Descriptive Analysis for {db_name}",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'family': 'Arial, sans-serif'}
        },
        height=800,
        # Remove fixed width to allow responsive sizing
        # width=1800,
        showlegend=False,
        margin=dict(l=10, r=10, t=80, b=10),  # Increased top margin to accommodate title
        font=dict(size=12),
        autosize=True,  # Enable autosize for responsiveness
    )
    return fig

def create_subplots(fig: go.Figure):
    human_word_color = '#239d1e'
    bot_word_color = '#AA0880'

    create_cumulative_message_count_by_user(fig=fig,
                                            cumulative_counts_df=cumulative_counts_df,
                                            subplot_row=1,
                                            subplot_col=1)
    create_cumulative_word_count_plot(fig=fig,
                                      cumulative_counts_df=cumulative_counts_df,
                                      human_word_color=human_word_color,
                                      bot_word_color=bot_word_color,
                                      subplot_row=2,
                                      subplot_col=1)


    # create_threads_per_user_histogram_subplot
    create_histogram_subplot(
        fig=fig,
        data=augmented_users_df['threads_participated'],
        subplot_row=1,
        subplot_col=4,
        x_label='Thread Count',
        color='#FFA15A',
        units='Threads',
    )

    # create_messages_per_user_histogram_subplot
    create_histogram_subplot(
        fig=fig,
        data=augmented_users_df['total_messages_sent'],
        subplot_row=1,
        subplot_col=5,
        x_label='Message Count',
        color='#19D3F3',
        units='Messages',
    )

    # create_words_per_user_histogram_subplot
    create_histogram_subplot(
        fig=fig,
        data=augmented_users_df['total_words_sent'],
        subplot_row=1,
        subplot_col=6,
        x_label='Word Count',
        color='#FF6692',
        units='Words',
        number_of_bins=50
    )

    # create_messages_per_thread_histogram_subplot
    create_histogram_subplot(
        fig=fig,
        data=human_messages_df.groupby('thread_id').size(),
        subplot_row=1,
        subplot_col=7,
        x_label='Message Count',
        color='#F3AEFA',
        units='Messages',
    )

    # create_words_per_message_histogram_subplot
    create_histogram_subplot(
        fig=fig,
        data=human_messages_df['human_word_count'],
        subplot_row=2,
        subplot_col=4,
        x_label='Word Count',
        color=human_word_color,
        max_bin=500,
        min_bin=0,
        number_of_bins=250,
        units='Words',
    )
    # create_words_per_message_histogram_subplot
    create_histogram_subplot(
        fig=fig,
        data=human_messages_df['bot_word_count'][human_messages_df['bot_word_count'] > 2],
        subplot_row=2,
        subplot_col=6,
        x_label='Word Count',
        color=bot_word_color,
        max_bin=500,
        min_bin=0,
        number_of_bins=250,
        units='Words',
    )


# Initialize the Dash app
app = Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# Define the app layout
app.layout = html.Div([
    html.Div([
        # Removed the title div since it's now part of the figure
        
        html.Div([
            dcc.Graph(
                id='main-graph',
                className="main-graph-container",
                config={'displayModeBar': True, 'responsive': True}
            ),
        ], style={'margin': '0px 0'}),

        html.Div([
            dcc.Interval(
                id='interval-component',
                interval=10 * 1000,  # in milliseconds (10 seconds)
                n_intervals=0
            )
        ]),
    ], style={ 'margin': '0 auto', 'padding': '0px'})
], style={'fontFamily': 'Arial, sans-serif'})

# Define callback to update the graph
@app.callback(
    Output('main-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    db_directory = Path(get_most_recent_db_location())
    db_name = db_directory.stem.replace("_data", "")
    fig = initialize_figure(db_name=db_name)
    create_subplots(fig)
    return fig



if __name__ == "__main__":
    # Generate and save static versions of the visualization
    logger.info("Generating static visualization files")
    _db_directory = Path(get_most_recent_db_location())
    _db_name = _db_directory.stem.replace("_data", "")
    visualization_name = f"{_db_name}_skellybot_visualization"

    static_fig = initialize_figure(db_name=_db_name)
    create_subplots(static_fig)

    # Save as HTML
    html_path = _db_directory / f"{visualization_name}.html"
    static_fig.write_html(str(html_path))
    logger.info(f"Saved HTML visualization to {html_path}")

    # Run the Dash app if not in static-only mode
    logger.info("Starting Dash app...")
    app.run_server(debug=True)