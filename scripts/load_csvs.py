#%%
import pandas as pd
from pathlib import Path

# db_path = Path(r"C:\Users\jonma\Sync\skellybot-data\skb-test_data")
db_path = Path(r"C:\Users\jonma\Sync\skellybot-data\H_M_N_2_5_data")

raw_users_df = pd.read_csv(db_path /"raw"/ "users.csv")
raw_messages_df = pd.read_csv(db_path /"raw"/ "messages.csv")
raw_threads_df = pd.read_csv(db_path /"raw"/ "threads.csv")
raw_context_prompts_df = pd.read_csv(db_path /"raw"/ "contextprompts.csv")

augmented_messages_df = pd.read_csv(db_path /"augmented_messages.csv")
augmented_threads_df = pd.read_csv(db_path /"augmented_threads.csv")
augmented_users_df = pd.read_csv(db_path /"augmented_users.csv")
cumulative_counts_df = pd.read_csv(db_path /"cumulative_counts.csv")
human_messages_df = pd.read_csv(db_path /"human_messages.csv")
ai_thread_analysis_df = pd.read_csv(db_path /"ai_thread_analyses.csv")
#%%