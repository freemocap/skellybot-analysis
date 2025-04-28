from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel

from skellybot_analysis.db.parquet_db.parquet_server_models import ParquetDiscordThread,ParquetDiscordMessage, ParquetDiscordUser, ParquetContextPrompt

import logging
logger = logging.getLogger(__name__)

class ParquetStorage:
    """Manages batched writes to Parquet with Pydantic validation"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self._base_name = self.output_dir.name.replace("_data", "")
        self._reset_buffers()

    def _reset_buffers(self):
        """Initialize empty buffers for all entity types"""
        self.threads: dict[int, ParquetDiscordThread] = {}
        self.messages: dict[int, ParquetDiscordMessage] = {}
        self.users: dict[int, ParquetDiscordUser] = {}
        self.prompts: dict[int, ParquetContextPrompt] = {}

    def save(self, db_id: int | str, entity: BaseModel):
        """Buffer validated entity for batch writing"""
        if isinstance(entity, ParquetDiscordThread):
            self.threads[db_id] = entity
        elif isinstance(entity, ParquetDiscordMessage):
            self.messages[db_id] = entity
        elif isinstance(entity, ParquetDiscordUser):
            self.users[db_id] = entity
        elif isinstance(entity, ParquetContextPrompt):
            self.prompts[db_id] = entity
        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")


    async def flush(self):
        """Write all buffered data to Parquet"""
        logger.info("Writing data to Parquet files...")


        logger.info(f"Writing {len(self.threads)} threads...")
        self._write_entity('users', list(self.users.values()))

        logger.info(f"Writing {len(self.messages)} messages...")
        self._write_entity('messages', list(self.messages.values()))

        logger.info(f"Writing {len(self.threads)} threads...")
        self._write_entity('threads', list(self.threads.values()))

        logger.info(f"Writing {len(self.prompts)} prompts...")
        self._write_entity('prompts', list(self.prompts.values()))
        logger.info("All data written to Parquet files!")
        self._reset_buffers()

    def _write_entity(self, name: str, data: list[BaseModel]):
        if not data:
            return

        df = pd.DataFrame([item.model_dump() for item in data])
        table = pa.Table.from_pandas(df)

        write_path = self.output_dir / f"{name}.parquet"

        pq.write_table(
            table,
            where=write_path,
            compression='ZSTD'
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.flush()
