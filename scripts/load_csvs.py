#%%
import pandas as pd
from pathlib import Path

# db_path = Path(r"C:\Users\jonma\Sync\skellybot-data\skb-test_data")
db_path = Path(r"C:\Users\jonma\Sync\skellybot-data\H_M_N_2_5_data")



ai_thread_analysis_df = pd.read_csv(db_path /"ai_thread_analyses.csv")
raw_users_df = pd.read_csv(db_path / "users.csv")
raw_context_prompts_df = pd.read_csv(db_path / "contextprompts.csv")
raw_messages_df = pd.read_csv(db_path / "messages.csv")
raw_threads_df = pd.read_csv(db_path / "threads.csv")

augmented_messages_df = pd.read_csv(db_path /"augmented_messages.csv")
augmented_threads_df = pd.read_csv(db_path /"augmented_threads.csv")
augmented_users_df = pd.read_csv(db_path /"augmented_users.csv")
cumulative_counts_df = pd.read_csv(db_path /"cumulative_counts.csv")
human_messages_df = pd.read_csv(db_path /"human_messages.csv")
embedding_projections_pca_df = pd.read_csv(db_path /"embedding_projections.csv")


# # Convert datetime columns to datetime objects
raw_messages_df['timestamp'] = pd.to_datetime(raw_messages_df['timestamp'],format="ISO8601")
augmented_messages_df['timestamp'] = pd.to_datetime(augmented_messages_df['timestamp'],format="ISO8601")

raw_users_df['joined_at'] = pd.to_datetime(raw_users_df['joined_at'],format="ISO8601")
augmented_users_df['joined_at'] = pd.to_datetime(augmented_users_df['joined_at'],format="ISO8601")

raw_threads_df['created_at'] = pd.to_datetime(raw_threads_df['created_at'],format="ISO8601")
augmented_threads_df['created_at'] = pd.to_datetime(augmented_threads_df['created_at'],format="ISO8601")

cumulative_counts_df['timestamp'] = pd.to_datetime(cumulative_counts_df['timestamp'],format="ISO8601")

human_messages_df['timestamp'] = pd.to_datetime(human_messages_df['timestamp'],format="ISO8601")





#%%