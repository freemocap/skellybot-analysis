import pandas as pd

from skellybot_analysis.df_db.df_augmentation.dataframe_augmentation import logger


def augment_threads(threads_df: pd.DataFrame,
                    human_messages_df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment threads with message counts and word counts.
    """
    logger.info("Augmenting threads with message and word counts")

    # Make a copy to avoid modifying the original
    df = threads_df.copy()

    # # Add context prompts to threads
    # df['context_prompt'] = df.map(
    #     context_prompts_df.set_index('context_id')['prompt_text']
    # )


    # Add total word count to threads
    df['total_word_count'] = df['thread_id'].map(
        human_messages_df.groupby('thread_id')['total_word_count'].sum()
    )

    # Add bot word count to threads
    bot_word_counts = human_messages_df.groupby('thread_id')['bot_word_count'].sum()
    df['bot_word_count'] = df['thread_id'].map(bot_word_counts)

    # Add human word count to threads
    human_word_counts = human_messages_df.groupby('thread_id')['human_word_count'].sum()
    df['human_word_count'] = df['thread_id'].map(human_word_counts)

    # Add human message count to threads
    message_counts = human_messages_df.groupby('thread_id').size()
    df['message_count'] = df['thread_id'].map(message_counts)

    # Add 'threads_participated' column
    df['threads_participated'] = df['thread_id'].map(
        human_messages_df.groupby('thread_id')['author_id'].nunique()
    )
    return df
