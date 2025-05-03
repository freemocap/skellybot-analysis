import logging
from typing import Tuple

import pandas as pd

from skellybot_analysis.df_db.df_augmentation.df_utils import count_words, combine_bot_messages
from skellybot_analysis.utilities.load_env_variables import PROF_USER_ID

logger = logging.getLogger(__name__)


def augment_messages(messages_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Augment the messages dataframe with word counts and create human messages dataframe.

    Returns:
        Tuple of (augmented_messages_df, human_messages_df)
    """
    logger.info("Augmenting messages with word counts")

    # Make a copy to avoid modifying the original
    df = messages_df.copy()

    # Remove professor messages
    df = df[df['author_id'] != PROF_USER_ID]

    # Convert timestamp to datetime if it isn't already
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Sort messages by timestamp
    df = df.sort_values('timestamp')

    # Add word count to messages
    df['word_count'] = df['content'].apply(count_words)

    # Create human and bot message dataframes
    human_messages_df = df[~df['bot_message']].copy()

    # Find bot responses to human messages using the improved function
    human_messages_df['bot_response'] = human_messages_df['message_id'].apply(
        lambda msg_id: combine_bot_messages(df, msg_id)
    )

    # Combine message and response
    human_messages_df['message_and_response'] = (
            human_messages_df['content'] + '\n\n' +
            human_messages_df['bot_response'].fillna('')
    )

    # add total_word_count, human_word_count, and bot_word_count to human messages
    human_messages_df['total_word_count'] = human_messages_df['message_and_response'].apply(count_words)
    human_messages_df['human_word_count'] = human_messages_df['full_content'].apply(count_words)
    human_messages_df['bot_word_count'] = human_messages_df['bot_response'].apply(count_words)

    return df, human_messages_df
