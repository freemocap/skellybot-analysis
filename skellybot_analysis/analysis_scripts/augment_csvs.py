# %% Import stuff 
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import os

# %% Set data folder
data_folder = "C:/Users/jonma/Sync/skellybot-data/H_M_N_2_5_data"
base_name = Path(data_folder).stem.replace('_data', '')

skellybot_id  = 1186697433674166293 # DISCORD_BOT_ID
prof_id = 362711467104927744 
# %% create csv paths
users_path = Path(data_folder) / f"{base_name}_users.csv"
messages_path = Path(data_folder) / f"{base_name}_messages.csv"
threads_path = Path(data_folder) / f"{base_name}_threads.csv"
analyses_path = Path(data_folder) / f"{base_name}_analyses.csv"
for thing in [users_path, messages_path, threads_path, analyses_path]:
    if not thing.exists():
        raise FileNotFoundError(f"File not found: {thing}")

# %% Load data
users_df = pd.read_csv(users_path)
messages_df = pd.read_csv(messages_path)
threads_df = pd.read_csv(threads_path)
analyses_df = pd.read_csv(analyses_path)

# remove Bot and Prof from Users df
users_df = users_df[users_df['id'] != skellybot_id]
users_df = users_df[users_df['id'] != prof_id]

# drop columns that are not needed
users_df.drop(columns=['created_at'], inplace=True)
users_df.drop(columns=['is_bot'], inplace=True)
messages_df.drop(columns=['created_at'], inplace=True)
threads_df.drop(columns=['created_at'], inplace=True)
analyses_df.drop(columns=['created_at'], inplace=True)

users_df.drop(columns=['name'], inplace=True) #drop username to partially de-identify users

# %% Add word count to messages
def count_words(text):
    if pd.isna(text):
        return 0
    return len(str(text).split())

messages_df['word_count'] = messages_df['content'].apply(count_words)

# %% Add total/bot/human word count to threads
threads_df['total_word_count'] = threads_df['id'].map(messages_df.groupby('thread_id')['word_count'].sum())
bot_word_counts = messages_df[messages_df['is_bot']==True].groupby('thread_id')['word_count'].sum()
threads_df['bot_word_count'] = threads_df['id'].map(bot_word_counts)
human_word_counts = messages_df[messages_df['is_bot']==False].groupby('thread_id')['word_count'].sum()
threads_df['human_word_count'] = threads_df['id'].map(human_word_counts)

# %% Add (Human) Message count to threads
message_counts = messages_df[messages_df['is_bot']==False].groupby('thread_id').size()
threads_df['message_count'] = threads_df['id'].map(message_counts)

# %% Group messages by user and calculate word, message, and thread counts
# Create aggregation by owner_id from threads_df


# Count total messages per user
messages_by_user = messages_df.groupby('author_id') 
message_counts_by_user = messages_by_user.size().reset_index(name='total_messages_sent')
users_df = users_df.merge(message_counts_by_user, how='left', left_on='id', right_on='author_id')
if 'author_id' in users_df.columns:
    users_df = users_df.drop('author_id', axis=1)

# Count unique threads per user
thread_counts_by_user = messages_df.groupby('author_id')['thread_id'].nunique().reset_index(name='threads_participated')
users_df = users_df.merge(thread_counts_by_user, how='left', left_on='id', right_on='author_id')
if 'author_id' in users_df.columns:
    users_df = users_df.drop('author_id', axis=1)

# Count total words per user
words_sent_by_user = messages_df.groupby('author_id')['word_count'].sum().reset_index(name='total_words_sent')
users_df = users_df.merge(words_sent_by_user, how='left', left_on='id', right_on='author_id')
if 'author_id' in users_df.columns:
    users_df = users_df.drop('author_id', axis=1)
# words_received_by_user = ??? # Calc # words sent to user by bot by looking for messages that the bot sent where the `parent_message_id` is in the user's messages
# %%
users_df['id'] = users_df['id'].astype(str).str[-6:].astype(int) # replace user ids with last 6 digits of their id to de-identify users
users_df['id'].rename('user_id', inplace=True) # rename id to user_id

# %% 