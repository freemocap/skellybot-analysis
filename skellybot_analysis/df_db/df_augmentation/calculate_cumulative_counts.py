import pandas as pd

import logging
logger = logging.getLogger(__name__)

def calculate_cumulative_counts(human_messages_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate running cumulative message count per user and total across all users.
    Also calculate cumulative word counts (total, human, and bot).
    """
    logger.info("Calculating cumulative message counts and word counts")

    # Sort messages by timestamp
    sorted_df = human_messages_df.sort_values('timestamp')

    # Calculate running cumulative count for each user
    user_cumulative = (
        sorted_df.groupby(['author_id', 'timestamp']).size()
        .groupby(level=0).cumsum()
        .reset_index()
    )
    user_cumulative.columns = ['author_id', 'timestamp', 'cumulative_message_count']

    # Calculate total cumulative count across all users
    total_cumulative = (
        sorted_df.groupby('timestamp').size()
        .cumsum()
        .reset_index()
    )
    total_cumulative.columns = ['timestamp', 'total_cumulative_count']

    # Calculate cumulative word counts
    # Total words (human + bot)
    total_word_cumulative = (
        sorted_df.groupby('timestamp')['total_word_count'].sum()
        .cumsum()
        .reset_index()
    )
    total_word_cumulative.columns = ['timestamp', 'cumulative_total_word_count']

    # Human words only
    human_word_cumulative = (
        sorted_df.groupby('timestamp')['human_word_count'].sum()
        .cumsum()
        .reset_index()
    )
    human_word_cumulative.columns = ['timestamp', 'cumulative_human_word_count']

    # Bot words only
    bot_word_cumulative = (
        sorted_df.groupby('timestamp')['bot_word_count'].sum()
        .cumsum()
        .reset_index()
    )
    bot_word_cumulative.columns = ['timestamp', 'cumulative_bot_word_count']

    # Merge all the counts into one dataframe
    result = pd.merge(
        user_cumulative,
        total_cumulative,
        on='timestamp',
        how='left'
    )

    result = pd.merge(
        result,
        total_word_cumulative,
        on='timestamp',
        how='left'
    )

    result = pd.merge(
        result,
        human_word_cumulative,
        on='timestamp',
        how='left'
    )

    result = pd.merge(
        result,
        bot_word_cumulative,
        on='timestamp',
        how='left'
    )

    # Ensure timestamp is a datetime object
    if not pd.api.types.is_datetime64_any_dtype(result['timestamp']):
        result = result.copy()
        result['timestamp'] = pd.to_datetime(result['timestamp'])
    return result
