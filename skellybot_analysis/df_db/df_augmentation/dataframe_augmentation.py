import logging
from pathlib import Path

import pandas as pd

from skellybot_analysis.ai.analyze_server_data import ai_analyze_threads
from skellybot_analysis.ai.calculate_embeddings_and_projections import calculate_embeddings_and_projections, \
    EmbeddableItem
from skellybot_analysis.data_models.analysis_models import AiThreadAnalysisModel
from skellybot_analysis.df_db.df_augmentation.augment_messages import augment_messages
from skellybot_analysis.df_db.df_augmentation.augment_threads_df import augment_threads
from skellybot_analysis.df_db.df_augmentation.augment_users_df import augment_users
from skellybot_analysis.df_db.df_augmentation.calculate_cumulative_counts import calculate_cumulative_counts
from skellybot_analysis.df_db.dataframe_handler import DataframeHandler
from skellybot_analysis.data_models.server_models import ThreadId
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

logger = logging.getLogger(__name__)


async def augment_dataframes(dataframe_handler: DataframeHandler, skip_ai: bool = False, skip_embeddings:bool=False) -> None:

    logger.info("Starting dataframe augmentation")

    # Augment messages and create human messages
    augmented_messages_df, human_messages_df = augment_messages(dataframe_handler.messages_df)
    
    # Augment threads
    augmented_threads_df = augment_threads(threads_df=dataframe_handler.threads_df,
                                           human_messages_df=human_messages_df)
    
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

    if not skip_ai:
        # Run ai analyses on threads
        thread_analyses:dict[ThreadId, AiThreadAnalysisModel] = await ai_analyze_threads(dataframe_handler=dataframe_handler)
        [dataframe_handler.store(primary_id=thread_id,
                                 entity=analysis) for thread_id, analysis in thread_analyses.items()]
        dataframe_handler.save_raw_csvs()

    if not skip_embeddings:
        embeddable_items = []
        # Add messages
        for _, row in human_messages_df.iterrows():
            embeddable_items.append(
                EmbeddableItem.from_human_message_row(df_row=row,
                                                      index=len(embeddable_items))
            )
        # Add thread analyses
        for _, analysis in enumerate(dataframe_handler.thread_analyses.values()):
            embeddable_items.append(
                EmbeddableItem.from_thread_analysis(analysis=analysis,
                                                    index=len(embeddable_items)
                                                    )
            )
        embedded_items: list[EmbeddableItem] = await calculate_embeddings_and_projections(
            embeddable_items=embeddable_items,
        )
        embedding_projections_df: pd.DataFrame  = pd.DataFrame(
            [item.model_dump() for item in embedded_items]
        )
        embedding_projections_df.to_csv(base_path / f'embedding_projections_df.csv', index=False)

    logger.info("Dataframe augmentation completed")

if __name__ == "__main__":
    import asyncio
    _db_path = get_most_recent_db_location()
    df_handler = DataframeHandler.from_db_path(db_path=_db_path)
    asyncio.run(augment_dataframes(dataframe_handler=df_handler,
                                   skip_ai=True,
                                   skip_embeddings=False))
    print("Augmentation Done!")