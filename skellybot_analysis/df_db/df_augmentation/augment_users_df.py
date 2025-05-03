import pandas as pd

from skellybot_analysis.df_db.df_augmentation.dataframe_augmentation import logger
from skellybot_analysis.utilities.load_env_variables import PROF_USER_ID


def augment_users(users_df: pd.DataFrame, human_messages_df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment users with message counts, thread participation, and word counts.
    """
    logger.info("Augmenting users with activity metrics")

    # Make a copy to avoid modifying the original
    df = users_df.copy()

    # drop bot and prof
    df = df[~df['is_bot']]
    df = df[df['user_id']!= PROF_USER_ID]

    # Count total messages per user
    messages_by_user = human_messages_df.groupby('author_id')
    message_counts_by_user = messages_by_user.size().reset_index(name='total_messages_sent')
    df = df.merge(message_counts_by_user, how='left', left_on='user_id', right_on='author_id')

    # Remove the redundant 'author_id' column
    if 'author_id' in df.columns:
        df = df.drop('author_id', axis=1)

    # Count unique threads per user
    thread_counts_by_user = human_messages_df.groupby('author_id')['thread_id'].nunique().reset_index(
        name='threads_participated'
    )
    df = df.merge(thread_counts_by_user, how='left', left_on='user_id', right_on='author_id')

    if 'author_id' in df.columns:
        df = df.drop('author_id', axis=1)

    # Count total words per user (sent and received)
    words_sent_by_user = human_messages_df.groupby('author_id')['human_word_count'].sum().reset_index(
        name='total_words_sent'
    )
    df = df.merge(words_sent_by_user, how='left', left_on='user_id', right_on='author_id')

    words_received_by_user = human_messages_df.groupby('author_id')['bot_word_count'].sum().reset_index(
        name='total_words_received'
    )
    df = df.merge(words_received_by_user, how='left', left_on='user_id', right_on='author_id')

    if 'author_id' in df.columns:
        df = df.drop('author_id', axis=1)

    return df
