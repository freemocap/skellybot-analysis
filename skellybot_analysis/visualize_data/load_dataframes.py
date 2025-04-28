from pathlib import Path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd

from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location


def load_dataframes(data_folder:str|None =None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if data_folder is None:
        data_folder = Path(get_most_recent_db_location()).parent
    base_name = Path(data_folder).stem.replace('_data', '')
    users_path = Path(data_folder) / f"{base_name}_users_augmented.csv"
    messages_path = Path(data_folder) / f"{base_name}_messages_augmented.csv"
    threads_path = Path(data_folder) / f"{base_name}_threads_augmented.csv"
    cumulative_counts_path = Path(data_folder) / f"{base_name}_cumulative_counts.csv"
    analyses_df_path = Path(data_folder) / f"{base_name}_analyses_raw.csv"
    tsne3d_df_path = Path(data_folder) / f"{base_name}_embeddings_tsne_3d.csv"

    for thing in [users_path, messages_path, threads_path, cumulative_counts_path, analyses_df_path, tsne3d_df_path]:
        if not thing.exists():
            raise FileNotFoundError(f"File not found: {thing}")

    # %% Load/prep data
    users_df = pd.read_csv(users_path)
    messages_df = pd.read_csv(messages_path)
    threads_df = pd.read_csv(threads_path)
    cumulative_counts_df = pd.read_csv(cumulative_counts_path)
    analyses_df = pd.read_csv(analyses_df_path)
    tsne3d_df = pd.read_csv(tsne3d_df_path)

    # Convert timestamp to datetime
    messages_df['timestamp'] = pd.to_datetime(messages_df['timestamp'], format='ISO8601')
    # Sort messages by timestamp
    messages_df = messages_df.sort_values('timestamp')

    return users_df, messages_df, threads_df, cumulative_counts_df, analyses_df, tsne3d_df


users_df, messages_df, threads_df, cumulative_counts_df, analyses_df, tsne3d_df = load_dataframes()
f = 9
# %%