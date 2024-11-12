import logging
from pathlib import Path

from src.configure_logging import configure_logging
configure_logging()
from src.scrape_server.models.server_data_model import ServerData, EXCLUDED_USER_IDS
from src.utilities.get_most_recent_server_data import get_server_data
from src.utilities.sanitize_filename import sanitize_name

logger = logging.getLogger(__name__)

def save_as_markdown_directory(server_data:ServerData, output_directory: str) -> str:
    """
    creates a directory with structure like
    [server]/[category]/[channel]/[thread_name].md
     where the markdown files contain the chat data, formatted like this:
     ```
    # [thread_name]
    ## [message_author]
        [message_url]
        [message_content]
        [attachments]
    ## (etc for each message in the thread)
        ...
    ```
    """
    try:
        directory_path = Path(output_directory)
        save_path = directory_path / "markdown"
        save_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving server data as markdown to {save_path}")
        server_directory = save_path / sanitize_name(server_data.name)
        server_directory.mkdir(exist_ok=True, parents=True)

        # by user
        users_directory = server_directory / "by_user"
        users_directory.mkdir(exist_ok=True, parents=True)
        for user_key, user_data in server_data.users.items():
            if user_data.user_id in EXCLUDED_USER_IDS:
                logger.info(f"Skipping excluded user {user_data.name}")
                continue
            logger.info(f"Saving user {user_data.name}")
            user_filename = f"userid_{user_key}.md"
            user_file_path = users_directory / user_filename
            with open(str(user_file_path), 'w', encoding='utf-8') as f:
                f.write(user_data.as_full_text())

        # by category/channel/thread
        for category_key, category_data in server_data.categories.items():
            logger.info(f"Saving category {category_data.name}")
            clean_category_name = sanitize_name(category_data.name)
            category_directory = server_directory / clean_category_name
            category_directory.mkdir(exist_ok=True, parents=True)
            if category_data.ai_analysis:
                category_summary_file = category_directory / f"category_index_{clean_category_name}_ai_analysis.md"
                with open(category_summary_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {clean_category_name} AI Analysis\n\n")
                    f.write(f"{category_data.ai_analysis.to_string()}\n\n")
                logging.debug(f"Summary for category {category_data.name}:\n {category_data.ai_analysis.to_string()}"
                              f"\n\n--------------------------------------------------------------------------------\n\n")

            for channel_key, channel_data in category_data.channels.items():
                logger.info(f"Saving channel {channel_data.name}")
                clean_channel_name = sanitize_name(channel_data.name)
                channel_directory = category_directory / clean_channel_name
                channel_directory.mkdir(exist_ok=True, parents=True)
                if channel_data.ai_analysis:
                    channel_summary_file = channel_directory / f"channel_index_{clean_channel_name}_ai_analysis.md"
                    with open(channel_summary_file, 'w', encoding='utf-8') as f:
                        f.write(f"# {clean_channel_name} AI Analysis\n\n")
                        f.write(f"{channel_data.ai_analysis.to_string()}\n\n")
                    logger.debug(f"Summary for channel {channel_data.name}:\n {channel_data.ai_analysis.to_string()}"
                                 f"\n\n--------------------------------------------------------------------------------\n\n")

                for thread_key, thread_data in channel_data.chat_threads.items():
                    # if not thread_data.ai_analysis or not thread_data.ai_analysis.relevant:
                    #     logger.warning(f"Skipping irrelevant thread in channel {channel_data.name}: {thread_data.name} \n {thread_data.ai_analysis}")
                    #     continue
                    thread_file_name = f"{thread_data.ai_analysis.title}-{thread_data.id}.md"
                    thread_file_path = channel_directory / thread_file_name
                    logger.info(f"Saving thread {thread_data.name}")
                    with open(thread_file_path, 'w', encoding='utf-8') as f:
                        clean_thread_name = thread_key.replace('name:', '')
                        clean_thread_name = clean_thread_name.split(',id:')[0]
                        f.write(f"# {clean_thread_name}\n\n")
                        if thread_data.ai_analysis:
                            f.write(f"## AI Analysis\n\n")
                            f.write(f"{thread_data.ai_analysis.to_string()}\n\n")
                        for message_number, message in enumerate(thread_data.messages):
                            if message_number == 0:
                                f.write(f"## Starting ContentMessage\n\n")
                            elif message.is_bot:
                                f.write(f"## AI MESSAGE\n\n")
                            else:
                                f.write(f"## HUMAN MESSAGE\n\n")
                            f.write(f'> userid: {message.user_id}')
                            f.write(f"> {message.jump_url}\n\n")
                            f.write(f"{message.content}\n\n")
                            if message.attachments:
                                f.write("### Attachments:\n\n")
                                for attachment in message.attachments:
                                    f.write(f"{attachment}\n\n")
                            f.write("\n\n")

    except Exception as e:
        raise ValueError(f"Error saving server data as markdown: {e}")
    logger.info(f"Saved server data as markdown to {server_directory}!")
    return str(server_directory)

if __name__ == "__main__":

    logger.info("Saving server data as markdown directory")
    server_data, output_directory = get_server_data()
    save_as_markdown_directory(server_data, str(Path(output_directory).parent))