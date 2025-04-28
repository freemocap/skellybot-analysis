from pathlib import Path
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# %% Set data folder
data_folder = "C:/Users/jonma/Sync/skellybot-data/H_M_N_2_5_data"
base_name = Path(data_folder).stem.replace('_data', '')

# %% create csv paths
users_path = Path(data_folder) / f"{base_name}_users_augmented.csv"
messages_path = Path(data_folder) / f"{base_name}_messages_augmented.csv"
threads_path = Path(data_folder) / f"{base_name}_threads_augmented.csv"
cumulative_counts_path = Path(data_folder) / f"{base_name}_cumulative_counts.csv"

for thing in [users_path, messages_path, threads_path, cumulative_counts_path]:
    if not thing.exists():
        raise FileNotFoundError(f"File not found: {thing}")

# %% Load/prep data
users_df = pd.read_csv(users_path)
messages_df = pd.read_csv(messages_path)
threads_df = pd.read_csv(threads_path)
cumulative_counts_df = pd.read_csv(cumulative_counts_path)

# Create the subplot layout with correct distribution charts
fig = make_subplots(
    rows=2, cols=3,
    subplot_titles=(
        'Cumulative Message Count per User Over Time',
        'Distribution of Word Counts in Human Messages',
        'Distribution of Messages per User',
        'Distribution of Threads per User',
        'Distribution of Total Words per User',
    ),
    vertical_spacing=0.08,
    horizontal_spacing=0.1
)

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
        row=1, col=1
    )

# Message word count histogram 
human_messages = messages_df[messages_df['is_bot'] == False]
word_counts = human_messages['word_count']
hist_values, hist_bins = np.histogram(word_counts, bins=300, range=(0, 300))
max_frequency = hist_values.max()

fig.add_trace(
    go.Histogram(
        x=word_counts,
        nbinsx=300,
        marker_color='#636EFA',
        name='Word Count Frequency'
    ),
    row=1, col=2
)

# Update x-axis range for the histogram
fig.update_xaxes(range=[0, 300], row=1, col=2)

# Add vertical lines for mean and median in the histogram
mean_word_count = word_counts.mean()
median_word_count = word_counts.median()

fig.add_vline(x=mean_word_count, line_dash="dash", line_color="red", row=1, col=2)
fig.add_vline(x=median_word_count, line_dash="dash", line_color="green", row=1, col=2)

# Add annotations for mean and median
fig.add_annotation(
    x=mean_word_count,
    y=max_frequency * 0.9,
    text=f"Mean: {mean_word_count:.1f}",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="red",
    font=dict(color="red"),
    xref="x2", 
    yref="y2"
)

fig.add_annotation(
    x=median_word_count,
    y=max_frequency * 0.75,
    text=f"Median: {median_word_count:.1f}",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="green",
    font=dict(color="green"),
    xref="x2", 
    yref="y2"
)

# 1. Messages per user histogram
fig.add_trace(
    go.Histogram(
        x=users_df['total_messages_sent'],
        nbinsx=30,
        marker_color='#19D3F3',
        name='Messages per User'
    ),
    row=1, col=3
)
# Add mean/median lines for messages per user
mean_msgs = users_df['total_messages_sent'].mean()
median_msgs = users_df['total_messages_sent'].median()
fig.add_vline(x=mean_msgs, line_dash="dash", line_color="red", row=1, col=3)
fig.add_vline(x=median_msgs, line_dash="dash", line_color="green", row=1, col=3)

# 2. Threads per user histogram
fig.add_trace(
    go.Histogram(
        x=users_df['threads_participated'],
        nbinsx=20,
        marker_color='#FFA15A',
        name='Threads per User'
    ),
    row=2, col=1
)
# Add mean/median lines for threads per user
mean_threads = users_df['threads_participated'].mean()
median_threads = users_df['threads_participated'].median()
fig.add_vline(x=mean_threads, line_dash="dash", line_color="red", row=2, col=1)
fig.add_vline(x=median_threads, line_dash="dash", line_color="green", row=2, col=1)

# 3. Total words per user histogram
fig.add_trace(
    go.Histogram(
        x=users_df['total_words_sent'],
        nbinsx=20,
        marker_color='#FF6692',
        name='Words per User'
    ),
    row=2, col=2
)
# Add mean/median lines for words per user
mean_words = users_df['total_words_sent'].mean()
median_words = users_df['total_words_sent'].median()
fig.add_vline(x=mean_words, line_dash="dash", line_color="red", row=2, col=2)
fig.add_vline(x=median_words, line_dash="dash", line_color="green", row=2, col=2)

# Update axis labels
# Time series
fig.update_xaxes(title_text='Date', row=1, col=1)
fig.update_yaxes(title_text='Cumulative Message Count', row=1, col=1)

# Word count histogram
fig.update_xaxes(title_text='Word Count per Message', row=1, col=2)
fig.update_yaxes(title_text='Frequency', row=1, col=2)

# Messages per user
fig.update_xaxes(title_text='Messages Sent', row=1, col=3)
fig.update_yaxes(title_text='Number of Users', row=1, col=3)

# Threads per user
fig.update_xaxes(title_text='Threads Participated', row=2, col=1)
fig.update_yaxes(title_text='Number of Users', row=2, col=1)

# Words per user
fig.update_xaxes(title_text='Total Words Sent', row=2, col=2)
fig.update_yaxes(title_text='Number of Users', row=2, col=2)

# Update overall layout
fig.update_layout(
    height=720,
    width=1280,
    template='plotly_dark',
    showlegend=False,  # Hide legend to save space
    title=dict(
        text='User Activity Metrics and Distributions',
        font=dict(size=24)
    )
)

fig.show()