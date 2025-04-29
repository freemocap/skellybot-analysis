import logging
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from skellybot_analysis.models.analysis_models import AiThreadAnalysisModel
from skellybot_analysis.models.server_models import ThreadModel, MessageModel, UserModel, \
    ContextPromptModel, DataframeModel, ThreadId, MessageId, UserId, ContextId

logger = logging.getLogger(__name__)


class DataframeHandler(BaseModel):
    """Manages batched writes to Parquet with Pydantic validation"""
    db_path: str

    threads: dict[ThreadId, ThreadModel] = {}
    messages: dict[MessageId, MessageModel] = {}
    users: dict[UserId, UserModel] = {}
    prompts: dict[ContextId, ContextPromptModel] = {}

    thread_analyses: dict[ThreadId, AiThreadAnalysisModel] = {}


    @property
    def base_name(self):
        return self.output_dir.name.replace("_data", "")

    def store(self, primary_id: int | str, entity: BaseModel):
        """Buffer validated entity for batch writing"""
        if isinstance(entity, ThreadModel):
            self.threads[primary_id] = entity
        elif isinstance(entity, MessageModel):
            self.messages[primary_id] = entity
        elif isinstance(entity, UserModel):
            self.users[primary_id] = entity
        elif isinstance(entity, ContextPromptModel):
            self.prompts[primary_id] = entity
        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")


    async def save_to_csvs(self):
        """Write all buffered data to csv"""
        logger.info("Writing data to csv files...")

        logger.info(f"Writing {len(self.threads)} threads...")
        self._write_dataframe_to_csv( list(self.users.values()))

        logger.info(f"Writing {len(self.messages)} messages...")
        self._write_dataframe_to_csv( list(self.messages.values()))

        logger.info(f"Writing {len(self.threads)} threads...")
        self._write_dataframe_to_csv(list(self.threads.values()))

        logger.info(f"Writing {len(self.prompts)} prompts...")
        self._write_dataframe_to_csv(list(self.prompts.values()))

        logger.info("All data written to disk")


    def _write_dataframe_to_csv(self, data: list[DataframeModel]):
        if not data:
            return
        save_path = Path(self.db_path) / f"{data[0].df_filename()}"

        try:
            data_list = [item.model_dump() for item in data]
            df = pd.DataFrame(data_list)
            df.to_csv(str(save_path), index=False)
        except Exception as e:
            logger.error(f"Problem saving {save_path} -` {e}`")
            raise

        logger.info(f"Successfully saved {len(data_list)} rows to `{data[0].df_filename()}`")
