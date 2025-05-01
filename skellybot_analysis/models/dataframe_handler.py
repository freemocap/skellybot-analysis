import logging
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel

from skellybot_analysis.models.analysis_models import AiThreadAnalysisModel
from skellybot_analysis.models.server_models import ThreadModel, MessageModel, UserModel, \
    ContextPromptModel, DataframeModel, ThreadId, MessageId, UserId, ContextId

logger = logging.getLogger(__name__)


def model_list_to_dataframe(data: list[DataframeModel]) -> pd.DataFrame:
    """Convert a list of DataframeModel instances to a DataFrame"""
    if not data:
        return pd.DataFrame()
    return pd.DataFrame([item.model_dump() for item in data])


class DataframeHandler(BaseModel):
    """Manages batched writes to Parquet with Pydantic validation"""
    db_path: str

    threads: dict[ThreadId, ThreadModel] = {}
    messages: dict[MessageId, MessageModel] = {}
    users: dict[UserId, UserModel] = {}
    prompts: dict[ContextId, ContextPromptModel] = {}

    thread_analyses: dict[ThreadId, AiThreadAnalysisModel] = {}

    @property
    def messages_df(self) -> pd.DataFrame:
        """Convert messages to DataFrame"""
        return model_list_to_dataframe(list(self.messages.values()))

    @property
    def threads_df(self) -> pd.DataFrame:
        """Convert threads to DataFrame"""
        return model_list_to_dataframe(list(self.threads.values()))

    @property
    def users_df(self) -> pd.DataFrame:
        """Convert users to DataFrame"""
        return model_list_to_dataframe(list(self.users.values()))

    @property
    def prompts_df(self) -> pd.DataFrame:
        """Convert prompts to DataFrame"""
        return model_list_to_dataframe(list(self.prompts.values()))

    @property
    def thread_analyses_df(self) -> pd.DataFrame:
        """Convert thread analyses to DataFrame"""
        return model_list_to_dataframe(list(self.thread_analyses.values()))

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
        elif isinstance(entity, AiThreadAnalysisModel):
            self.thread_analyses[primary_id] = entity
        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")

    def save_raw_csvs(self):
        """Write all buffered data to csv"""
        logger.info("Writing data to csv files...")

        # Save and verify users
        self.thread_analyses_df.to_csv(Path(self.db_path) / AiThreadAnalysisModel.df_filename(), index=False)
        base_save_path = Path(self.db_path)
        base_save_path.mkdir(parents=True, exist_ok=True)
        self.users_df.to_csv(base_save_path / UserModel.df_filename(), index=False)
        self.messages_df.to_csv(base_save_path / MessageModel.df_filename(), index=False)
        self.threads_df.to_csv(base_save_path / ThreadModel.df_filename(), index=False)
        self.prompts_df.to_csv(base_save_path / ContextPromptModel.df_filename(), index=False)
        self._validate_data()

        logger.info("All data written and verified successfully")

    def _validate_data(self):
        loaded_instance = self.from_db_path(self.db_path)
        if not loaded_instance:
            logger.error("Failed to load data from CSV files")
            raise ValueError("Failed to load data from CSV files")

        for loaded_user_id, loaded_user in loaded_instance.users.items():
            if loaded_user_id not in self.users:
                logger.error(f"User {loaded_user_id} not found in original data")
                raise ValueError(f"User {loaded_user_id} not found in original data")

            if loaded_user != self.users[loaded_user_id]:
                logger.error(f"User {loaded_user_id} data mismatch - {loaded_user} != {self.users[loaded_user_id]}")
                raise ValueError(f"User {loaded_user_id} data mismatch")

    @classmethod
    def from_db_path(cls, db_path: str):
        """Load all CSV data into model dictionaries"""
        logger.info("Loading data from db_path...")
        db_path = Path(db_path)
        if not db_path.exists():
            logger.error(f"Database path {db_path} does not exist")
            raise ValueError(f"Database path {db_path} does not exist")
        instance = cls(db_path=str(db_path))
        instance._load_model_data(model_cls=UserModel,
                                  target_dict=instance.users,
                                  id_field="user_id")
        instance._load_model_data(model_cls=MessageModel,
                                  target_dict=instance.messages,
                                  id_field="message_id")
        instance._load_model_data(model_cls=ThreadModel,
                                  target_dict=instance.threads,
                                  id_field="thread_id")
        instance._load_model_data(model_cls=ContextPromptModel,
                                  target_dict=instance.prompts,
                                  id_field="context_id")
        try:
            instance._load_model_data(model_cls=AiThreadAnalysisModel,
                                      target_dict=instance.thread_analyses,
                                      id_field="thread_id")
        except ValueError:
            logger.warning("No thread analyses found in the database - skipping")
            instance.thread_analyses = {}
        return instance

    def _load_model_data(self, model_cls: type[DataframeModel], target_dict: dict[int, BaseModel],
                         id_field: str) -> pd.DataFrame:
        """Generic loader for any DataFrame-backed model"""
        csv_path = Path(self.db_path) / model_cls.df_filename()

        if not csv_path.exists():
            logger.warning(f"CSV file {csv_path.name} not found")
            raise ValueError(f"CSV file {csv_path.name} not found")

        try:
            df = pd.read_csv(csv_path)
            records = df.replace({np.nan: None}).to_dict(orient='records')
            target_dict.update({
                int(record[id_field]): model_cls.model_validate(record)
                for record in records
            })
            logger.info(f"Loaded {len(records)} {model_cls.__name__} from {csv_path.name}")
            return df
        except Exception as e:
            logger.error(f"Failed to load {model_cls.__name__} from {csv_path}: {e}")
            raise


if __name__ == "__main__":
    _db_path = r"C:\Users\jonma\Sync\skellybot-data\H_M_N_2_5_data"
    df_handler = DataframeHandler.from_db_path(_db_path)
    print(f"Loaded {len(df_handler.messages)} messages")
    print(f"Loaded {len(df_handler.users)} users")
    print(f"Loaded {len(df_handler.threads)} threads")
    print(f"Loaded {len(df_handler.prompts)} prompts")

    df_handler.save_raw_csvs()
