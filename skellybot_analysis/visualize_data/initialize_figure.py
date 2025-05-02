import logging

from plotly.subplots import make_subplots

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