# %% Import stuff 
from pathlib import Path
import numpy as np
import pandas as pd
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# %% Set data folder
data_folder = "C:/Users/jonma/Sync/skellybot-data/H_M_N_2_5_data"
base_name = Path(data_folder).stem.replace('_data', '')
skellybot_id = 1186697433674166293
prof_id = 362711467104927744

# %% create csv paths
users_path = Path(data_folder) / f"{base_name}_users_raw.csv"
messages_path = Path(data_folder) / f"{base_name}_messages_raw.csv"
threads_path = Path(data_folder) / f"{base_name}_threads_raw.csv"
analyses_path = Path(data_folder) / f"{base_name}_analyses_raw.csv"
for thing in [users_path, messages_path, threads_path, analyses_path]:
    if not thing.exists():
        raise FileNotFoundError(f"File not found: {thing}")

# %% Load/prep data
users_df = pd.read_csv(users_path)
messages_df = pd.read_csv(messages_path)
threads_df = pd.read_csv(threads_path)
analyses_df = pd.read_csv(analyses_path)

# Convert timestamp to datetime
messages_df['timestamp'] = pd.to_datetime(messages_df['timestamp'], format='ISO8601')
# Sort messages by timestamp
messages_df = messages_df.sort_values('timestamp')
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

# %% Create Human message + bot-response df
human_messages_df = messages_df[messages_df['is_bot'] == False].copy()
bot_messages_df = messages_df[messages_df['is_bot'] == True].copy()

# make sure that all human messages have a corresponding bot message (i.e. for every human message, there is a bot message that has a parent_message_id that opints to it)

for index, row in human_messages_df.iterrows():
    # get the bot message that is a response to this human message
    bot_response = bot_messages_df[bot_messages_df['parent_message_id'] == row['id']]
    # if there is no bot response, drop the human message
    if bot_response.empty:
        print(f"Human message {row['id']} has no bot response!!")


# merge the bot response that are split across mutliple messages by finding the bot messages that share a parent message, sorting by timestamp, and then concatenating the content
human_messages_df['bot_response'] = human_messages_df['id'].map(
    bot_messages_df.groupby('parent_message_id')['content'].apply(lambda x: '\n\n'.join(x))
)
human_messages_df['message_and_response'] = human_messages_df['content'] + '\n\n' + human_messages_df['bot_response']

# %% Count total messages per user
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


# %% Calculate running cumulative message count per user
# Calculate running cumulative count for each user
cumulative_counts = messages_df[messages_df['is_bot']==False].groupby(['author_id', 'timestamp']).size().groupby(level=0).cumsum().reset_index()
cumulative_counts.columns = ['author_id', 'timestamp', 'cumulative_message_count']

cumulative_counts = cumulative_counts[cumulative_counts['author_id'] != skellybot_id] # remove bot messages from cumulative counts
cumulative_counts = cumulative_counts[cumulative_counts['author_id'] != prof_id] # remove prof messages from cumulative counts

# %% Calculate embeddings and projections
from add_embedding_xyz import calculate_embeddings_and_projections
embeddings_npy ,embeddings_df = asyncio.run(calculate_embeddings_and_projections(human_messages_df=human_messages_df, thread_analyses_df=analyses_df))

# %% save dataframes to csvs (add `_augmented` to the filename)
# Save the augmented DataFrames to new CSV files
users_df.to_csv(users_path.with_stem(f"{base_name}_users_augmented"), index=False)
messages_df.to_csv(messages_path.with_stem(f"{base_name}_messages_augmented"), index=False)
human_messages_df.to_csv(messages_path.with_stem(f"{base_name}_human_messages"), index=False)
threads_df.to_csv(threads_path.with_stem(f"{base_name}_threads_augmented"), index=False)
cumulative_counts.to_csv(analyses_path.with_stem(f"{base_name}_cumulative_counts"), index=False)
embeddings_df.to_csv(analyses_path.with_stem(f"{base_name}_embeddings"), index=False)

# Save the numpy array to a .npy file
embeddings_npy_path = analyses_path.with_stem(f"{base_name}_embeddings").with_suffix('.npy')
np.save(embeddings_npy_path, embeddings_npy)


#%% Save the augmented DataFrames to new CSV files