#%%
import pandas as pd
from pathlib import Path

# db_path = Path(r"C:\Users\jonma\Sync\skellybot-data\skb-test_data")
db_path = Path(r"C:\Users\jonma\Sync\skellybot-data\H_M_N_2_5_data")

users_df = pd.read_csv(db_path / "users.csv")
messages_df = pd.read_csv(db_path / "messages.csv")
threads_df = pd.read_csv(db_path / "threads.csv")
context_prompts_df = pd.read_csv(db_path / "contextprompts.csv")

#%%