import pandas as pd
from pathlib import Path
from typing import List, Dict, Type, TypeVar, Any
import pyarrow.parquet as pq

from skellybot_analysis.db.parquet_db.pq_models.parquet_server_models import (
    ParquetDiscordMessage,
    ParquetDiscordThread,
    ParquetDiscordUser,
    ParquetContextPrompt
)


# Example usage
def load_discord_messages(db_path: str) -> List[ParquetDiscordMessage]:
    """Load all Discord messages from the database"""
    messages_df = pq.read_table(db_path).to_pandas()
    return [
        ParquetDiscordMessage(**row) for row in messages_df.to_dict(orient='records')
    ]

if __name__ == "__main__":
    from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

    _db_path = get_most_recent_db_location()
    # Example usage
    messages = load_discord_messages(_db_path)
    print(f"Loaded {len(messages)} messages")
