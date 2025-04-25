import logging
from pathlib import Path

import pandas as pd

from skellybot_analysis import configure_logging
from skellybot_analysis.ai.embeddings_stuff.calculate_embeddings_and_tsne import EmbeddingAndTsneXYZ, \
    create_embedding_and_tsne_clusters
from skellybot_analysis.db.db_models.db_ai_analysis_models import ServerObjectAiAnalysis
from skellybot_analysis.db.db_models.db_server_models import Thread, User, Message
from skellybot_analysis.db.db_utilities import get_db_session

logger = logging.getLogger(__name__)
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
        text_to_embed = [analysis.full_text for analysis in analyses]
        # Calculate embeddings and TSNE coordinates
        embeddings_and_tsnes: list[EmbeddingAndTsneXYZ] = await create_embedding_and_tsne_clusters(text_to_embed,
                                                                                                   perplexity=10)

        # Create main dataframe with thread information and TSNE coordinates
        analysis_data = []
        thread_data = []
        user_data = []
        message_data = []
        for analysis, embedding_tsne in zip(analyses, embeddings_and_tsnes):
            analysis_data.append({
                **analysis.model_dump(),
                'x': embedding_tsne.tsne_xyz.x,
                'y': embedding_tsne.tsne_xyz.y,
                'z': embedding_tsne.tsne_xyz.z,
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
        analysis_df = pd.DataFrame(analysis_data)
        thread_df = pd.DataFrame(thread_data)
        user_df = pd.DataFrame(user_data)
        message_df = pd.DataFrame(message_data)

        # Save dataframes to CSV files
        db_name = Path(db_path).stem.replace('.sqlite', '')
        analysis_path = Path(db_path).parent / f"_{db_name}_analyses.csv"
        thread_path = Path(db_path).parent / f"_{db_name}_threads.csv"
        user_path = Path(db_path).parent / f"_{db_name}_users.csv"
        message_path = Path(db_path).parent / f"_{db_name}_messages.csv"

        analysis_df.to_csv(analysis_path, index=False)
        thread_df.to_csv(thread_path, index=False)
        user_df.to_csv(user_path, index=False)
        message_df.to_csv(message_path, index=False)


        logger.info(f"Dataframes saved to: \n {Path(db_path)/f'_{db_name}_analyses.csv'}, \n {Path(db_path)/f'_{db_name}_threads.csv'}, \n {Path(db_path)/f'_{db_name}_users.csv'}, \n {Path(db_path)/f'_{db_name}_messages.csv'}")


if __name__ == "__main__":
    import asyncio
    from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

    configure_logging()
    db_path = get_most_recent_db_location()
    asyncio.run(save_db_as_dataframes(db_path=db_path))
