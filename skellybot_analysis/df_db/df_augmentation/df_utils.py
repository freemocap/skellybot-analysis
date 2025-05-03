import pandas as pd


def count_words(text: str) -> int:
    """Count words in a text string, handling NaN values."""
    if pd.isna(text):
        return 0
    return len(str(text).split())


def combine_bot_messages(messages_df: pd.DataFrame, human_message_id: str) -> str:
    """
    Recursively combine all bot messages that are part of a response chain to a human message.

    Args:
        messages_df: DataFrame containing all messages
        human_message_id: The ID of the human message to find responses for

    Returns:
        Combined text of all bot responses in the chain
    """
    bot_messages = messages_df[messages_df['bot_message']]

    # Function to recursively collect all bot messages in the response chain
    def collect_responses(parent_id):
        # Get direct responses to this message
        direct_responses = bot_messages[bot_messages['parent_message_id'] == parent_id]

        if direct_responses.empty:
            return []

        all_responses = list(direct_responses['content'])

        # For each direct response, also collect any responses to it
        for msg_id in direct_responses['message_id']:
            all_responses.extend(collect_responses(msg_id))

        return all_responses

    # Start collection from the human message
    response_contents = collect_responses(human_message_id)

    # Combine all responses
    combined_content = '\n\n'.join(response_contents) if response_contents else ''

    # Clean up continuation markers
    cleaned_lines = []
    for line in combined_content.split('\n'):
        if line.strip().startswith("> continuing from"):
            continue
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)
