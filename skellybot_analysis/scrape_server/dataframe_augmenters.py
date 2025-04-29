import logging
from pathlib import Path

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional

from skellybot_analysis.ai.calculate_embeddings_and_projections import calculate_embeddings_and_projections
from skellybot_analysis.models.dataframe_handler import DataframeHandler

logger = logging.getLogger(__name__)



def count_words(text):
    """Count words in a text string, handling NaN values."""
    if pd.isna(text):
        return 0
    return len(str(text).split())

def augment_messages(messages_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Augment the messages dataframe with word counts and create human messages dataframe.
    
    Returns:
        Tuple of (augmented_messages_df, human_messages_df)
    """
    logger.info("Augmenting messages with word counts")
    
    # Make a copy to avoid modifying the original
    df = messages_df.copy()
    
    # Convert timestamp to datetime if it isn't already
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort messages by timestamp
    df = df.sort_values('timestamp')
    
    # Add word count to messages
    df['word_count'] = df['content'].apply(count_words)
    
    # Create human and bot message dataframes
    human_messages_df = df[~df['bot_message']].copy()
    bot_messages_df = df[df['bot_message']].copy()
    
    # Find bot responses to human messages
    human_messages_df['bot_response'] = human_messages_df['message_id'].map(
        bot_messages_df.groupby('parent_message_id')['content'].apply(
            lambda x: '\n\n'.join(x)
        )
    )
    
    # Combine message and response
    human_messages_df['message_and_response'] = (
        human_messages_df['content'] + '\n\n' + 
        human_messages_df['bot_response'].fillna('')
    )
    
    return df, human_messages_df

def augment_threads(threads_df: pd.DataFrame, messages_df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment threads with message counts and word counts.
    """
    logger.info("Augmenting threads with message and word counts")
    
    # Make a copy to avoid modifying the original
    df = threads_df.copy()
    
    # Add total word count to threads
    df['total_word_count'] = df['thread_id'].map(
        messages_df.groupby('thread_id')['word_count'].sum()
    )
    
    # Add bot word count to threads
    bot_word_counts = messages_df[messages_df['bot_message']].groupby('thread_id')['word_count'].sum()
    df['bot_word_count'] = df['thread_id'].map(bot_word_counts)
    
    # Add human word count to threads
    human_word_counts = messages_df[~messages_df['bot_message']].groupby('thread_id')['word_count'].sum()
    df['human_word_count'] = df['thread_id'].map(human_word_counts)
    
    # Add human message count to threads
    message_counts = messages_df[~messages_df['bot_message']].groupby('thread_id').size()
    df['message_count'] = df['thread_id'].map(message_counts)
    
    return df

def augment_users(users_df: pd.DataFrame, human_messages_df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment users with message counts, thread participation, and word counts.
    """
    logger.info("Augmenting users with activity metrics")
    
    # Make a copy to avoid modifying the original
    df = users_df.copy()
    
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
    
    # Count total words per user
    words_sent_by_user = human_messages_df.groupby('author_id')['word_count'].sum().reset_index(
        name='total_words_sent'
    )
    df = df.merge(words_sent_by_user, how='left', left_on='user_id', right_on='author_id')
    
    if 'author_id' in df.columns:
        df = df.drop('author_id', axis=1)
    
    return df

def calculate_cumulative_counts(human_messages_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate running cumulative message count per user.
    """
    logger.info("Calculating cumulative message counts")
    
    # Calculate running cumulative count for each user
    cumulative_counts = (
        human_messages_df.groupby(['author_id', 'timestamp']).size()
        .groupby(level=0).cumsum()
        .reset_index()
    )
    cumulative_counts.columns = ['author_id', 'timestamp', 'cumulative_message_count']
    
    return cumulative_counts

async def generate_embeddings(human_messages_df: pd.DataFrame, 
                             analyses_df: Optional[pd.DataFrame] = None) -> Tuple[np.ndarray, Dict[str, pd.DataFrame]]:
    """
    Generate embeddings and projections for the human messages.
    """
    logger.info("Generating embeddings and projections")
    
    if calculate_embeddings_and_projections is None:
        logger.warning("Embedding calculation is not available - skipping")
        return np.array([]), {}
    
    if analyses_df is None:
        analyses_df = pd.DataFrame()  # Empty dataframe if not provided
        
    embeddings_npy, embedding_dfs = await calculate_embeddings_and_projections(
        human_messages_df=human_messages_df, 
        thread_analyses_df=analyses_df
    )
    
    return embeddings_npy, embedding_dfs

async def augment_dataframes(dataframe_handler: DataframeHandler) -> Dict[str, pd.DataFrame]:

    logger.info("Starting dataframe augmentation")
    
    results = {}
    
    # Augment messages and create human messages
    augmented_messages_df, human_messages_df = augment_messages(dataframe_handler.messages_df)
    
    # Augment threads
    augmented_threads_df = augment_threads(dataframe_handler.threads_df, augmented_messages_df)
    
    # Augment users
    augmented_users_df = augment_users(dataframe_handler.users_df, human_messages_df)
    
    # Calculate cumulative counts
    cumulative_counts_df = calculate_cumulative_counts(human_messages_df)
    
    # Store results
    base_path = Path(dataframe_handler.db_path)
    augmented_messages_df.to_csv(base_path / 'augmented_messages.csv', index=False)
    human_messages_df.to_csv(base_path / 'human_messages.csv', index=False)
    augmented_threads_df.to_csv(base_path / 'augmented_threads.csv', index=False)
    augmented_users_df.to_csv(base_path / 'augmented_users.csv', index=False)
    cumulative_counts_df.to_csv(base_path / 'cumulative_counts.csv', index=False)
    
    # Generate embeddings if requested
    embeddings_npy, embedding_dfs = await generate_embeddings(human_messages_df, dataframe_handler.thread_analyses_df)
    for name, df in embedding_dfs.items():
        df.to_csv(base_path / f'embedding_projections_{name}.csv', index=False)
    
    logger.info("Dataframe augmentation completed")
    return results