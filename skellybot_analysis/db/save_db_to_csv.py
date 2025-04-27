import logging
from pathlib import Path

import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


from skellybot_analysis import configure_logging
from skellybot_analysis.db.db_models.db_ai_analysis_models import ServerObjectAiAnalysis
from skellybot_analysis.db.db_models.db_server_models import Thread, User, Message
from skellybot_analysis.db.db_utilities import get_db_session
from skellybot_analysis.utilities.load_env_variables import DISCORD_BOT_ID, PROF_USER_ID


logger = logging.getLogger(__name__)

def anonymize_id(df, column_name):
    """Helper function to consistently anonymize ID columns by taking last 6 digits"""
    df[column_name] = df[column_name].apply(
        lambda x: int(str(x)[-6:]) if x is not None and str(x) != 'None' else None
    )
    return df
async def save_db_as_dataframes(db_path: str | None=None) -> pd.DataFrame:
    """
    Create dataframes from thread analyses and their embeddings/TSNE coordinates

    Args:
        thread_analyses_df: DataFrame of ServerObjectAiAnalysis objects

    Returns:
        DataFrame with thread information and TSNE coordinates
    """
    with get_db_session(db_path=db_path) as session:
        analyses = session.query(ServerObjectAiAnalysis).all()
        threads = session.query(Thread).all()
        users = session.query(User).all()
        messages = session.query(Message).all()
        logger.info(f"Creating dataframes from: \n {len(analyses)} analyses, \n {len(threads)} threads, \n {len(users)} users, \n {len(messages)} messages")

        # Create main dataframe with thread information and TSNE coordinates
        analyses_data = []
        thread_data = []
        user_data = []
        message_data = []

        for analysis in analyses:
            analyses_data.append({
                **analysis.model_dump(),
            })

        for thread in threads:
            thread_data.append({
                **thread.model_dump(),
            })
        for user in users:
            user_data.append({
                **user.model_dump(),
            })
        for message in messages:
            message_data.append({
                **message.model_dump(),
            })

        # Create dataframes
        analyses_df = pd.DataFrame(analyses_data)
        threads_df = pd.DataFrame(thread_data)
        users_df = pd.DataFrame(user_data)
        messages_df = pd.DataFrame(message_data)


        # drop uneeded columns
        users_df.drop(columns=['created_at'], inplace=True)
        users_df.drop(columns=['is_bot'], inplace=True)
        messages_df.drop(columns=['created_at'], inplace=True)
        threads_df.drop(columns=['created_at'], inplace=True)
        analyses_df.drop(columns=['created_at'], inplace=True)

        # remove prof and bot from users
        users_df = users_df[users_df['id'] != DISCORD_BOT_ID]
        users_df = users_df[users_df['id'] != PROF_USER_ID]

        # de-id users
        users_df.drop(columns=['name'], inplace=True)

        # # Replace IDs with last 6 digits for anonymization
        # anonymize_id(users_df, 'id')
        # anonymize_id(threads_df, 'owner_id')
        # anonymize_id(messages_df, 'author_id')
        # anonymize_id(analyses_df, 'thread_owner_id')

        # deidentify_message_content(message_df)

        # Save dataframes to CSV files
        db_name = Path(db_path).stem.replace('.sqlite', '')
        analysis_path = Path(db_path).parent / f"{db_name}_analyses_raw.csv"
        thread_path = Path(db_path).parent / f"{db_name}_threads_raw.csv"
        user_path = Path(db_path).parent / f"{db_name}_users_raw.csv"
        message_path = Path(db_path).parent / f"{db_name}_messages_raw.csv"

        analyses_df.to_csv(analysis_path, index=False)
        threads_df.to_csv(thread_path, index=False)
        users_df.to_csv(user_path, index=False)
        messages_df.to_csv(message_path, index=False)


        logger.info(f"Dataframes saved to: \n {analysis_path}, \n {thread_path}, \n {user_path}, \n {message_path}")


if __name__ == "__main__":
    import asyncio
    from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

    configure_logging()
    db_path = get_most_recent_db_location()
    asyncio.run(save_db_as_dataframes(db_path=db_path))
