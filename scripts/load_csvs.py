#%%
import pandas as pd
from pathlib import Path

# db_path = Path(r"C:\Users\jonma\Sync\skellybot-data\skb-test_data")
db_path = Path(r"C:\Users\jonma\Sync\skellybot-data\H_M_N_2_5_data")



raw_users_df = pd.read_csv(db_path / "users.csv")
augmented_users_df = pd.read_csv(db_path /"augmented_users.csv")
raw_messages_df = pd.read_csv(db_path / "messages.csv")
augmented_messages_df = pd.read_csv(db_path /"augmented_messages.csv")
human_messages_df = pd.read_csv(db_path /"human_messages.csv")
raw_threads_df = pd.read_csv(db_path / "threads.csv")
augmented_threads_df = pd.read_csv(db_path /"augmented_threads.csv")
raw_context_prompts_df = pd.read_csv(db_path / "contextprompts.csv")
cumulative_counts_df = pd.read_csv(db_path /"cumulative_counts.csv")
ai_thread_analysis_df = pd.read_csv(db_path /"ai_thread_analyses.csv")
embedding_projections_tsne_2d_df = pd.read_csv(db_path /"embedding_projections_tsne_2d.csv")
embedding_projections_tsne_3d_df = pd.read_csv(db_path /"embedding_projections_tsne_3d.csv")
embedding_projections_umap_2d_df = pd.read_csv(db_path /"embedding_projections_umap_2d.csv")
embedding_projections_umap_3d_df = pd.read_csv(db_path /"embedding_projections_umap_3d.csv")
embedding_projections_pca_df = pd.read_csv(db_path /"embedding_projections_pca.csv")



#%%