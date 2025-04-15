import logging
from pathlib import Path

from skellybot_analysis.models.data_models.server_data.server_data_sub_object_models import ChatThread, ChannelData, \
    CategoryData
from skellybot_analysis.models.data_models.tag_models import TagManager
from skellybot_analysis.models.data_models.user_data_model import UserDataManager, UserData
from skellybot_analysis.system.logging_configuration.configure_logging import configure_logging

configure_logging()
from skellybot_analysis.models.data_models.server_data.server_data_model import ServerData, EXCLUDED_USER_IDS
from skellybot_analysis.utilities.sanitize_filename import sanitize_name

logger = logging.getLogger(__name__)


def save_tag_as_markdown(tag_model, topics_directory):
    if tag_model.ai_analysis is None:
        logger.info(f"Skipping tag {tag_model.name} because it has no AI analysis")
        return
    logger.info(f"Saving tag {tag_model.name}")
    tag_filename = f"{tag_model.name}.md"
    tag_file_path = topics_directory / tag_filename
    with open(str(tag_file_path), 'w', encoding='utf-8') as f:
        f.write(f"# {tag_model.name}\n\n")
        f.write(f"> Tag Link Count: {tag_model.link_count}\n\n")
        f.write(f"{tag_model.ai_analysis.to_string()}\n\n")
        f.write(f"## Threads with this tag\n\n")
        for thread in tag_model.tagged_threads:
            f.write(f"- [[by_server/{thread}]]\n")
        f.write("\n## Users with this tag\n\n")
        for user in tag_model.tagged_users:
            f.write(f"- [[ by_user/{user}]]\n")


def save_user_as_markdown(user_key: id,
                          user_data: UserData,
                          users_directory: Path):
    if user_data.id in EXCLUDED_USER_IDS:
        logger.info(f"Skipping excluded user {user_data.name}")
        return
    logger.info(f"Saving user {user_data.name}")
    user_filename = f"userid_{user_key}.md"
    user_file_path = users_directory / user_filename
    with open(str(user_file_path), 'w', encoding='utf-8') as f:
        f.write(f"# Summary for User: {user_data.name}\n\n")
        f.write(user_data.as_text())


def save_thread_as_markdown(thread_data:ChatThread,
                            channel_directory: Path):

    thread_file_path = channel_directory / thread_data.file_name()
    logger.info(f"Saving thread {thread_data.name}")
    with open(thread_file_path, 'w', encoding='utf-8') as f:
        f.write(thread_data.as_full_text())


def save_channel_as_markdown(channel_data: ChannelData,
                             category_directory: Path):
    logger.info(f"Saving channel {channel_data.name}")
    clean_channel_name = sanitize_name(channel_data.name)
    channel_directory = category_directory / clean_channel_name
    channel_directory.mkdir(exist_ok=True, parents=True)
    if channel_data.ai_analysis:
        channel_summary_file = channel_directory / f"channel_{clean_channel_name}_overview.md"
        with open(channel_summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# {clean_channel_name} AI Summary/Analysis\n\n")
            f.write(f"{channel_data.ai_analysis.to_string()}\n\n")
        logger.debug(f"Summary for channel {channel_data.name}:\n {channel_data.ai_analysis.to_string()}"
                     f"\n\n--------------------------------------------------------------------------------\n\n")
    for thread_key, thread_data in channel_data.chat_threads.items():
        save_thread_as_markdown(thread_data, channel_directory)


def save_category_as_markdown(category_data: CategoryData,
                              by_server_directory: Path):
    logger.info(f"Saving category {category_data.name}")
    clean_category_name = sanitize_name(category_data.name)
    category_directory = by_server_directory / clean_category_name
    category_directory.mkdir(exist_ok=True, parents=True)
    if category_data.ai_analysis:
        category_summary_file = category_directory / f"category_{clean_category_name}_overview.md"
        with open(category_summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# {clean_category_name} AI Summary/Analysis\n\n")
            f.write(f"{category_data.ai_analysis.to_string()}\n\n")
        logger.debug(f"Summary for category {category_data.name}:\n {category_data.ai_analysis.to_string()}"
                     f"\n\n--------------------------------------------------------------------------------\n\n")
    for channel_key, channel_data in category_data.channels.items():
        save_channel_as_markdown(channel_data, category_directory)


def save_server_data_as_markdown_directory(server_data: ServerData,
                                           user_data: UserDataManager,
                                           tag_data: TagManager,
                                           output_directory: str):
    save_path = Path(output_directory)

    save_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving server data as markdown to {save_path}")


    # by topic
    topics_directory = save_path / "by_topic"
    topics_directory.mkdir(exist_ok=True, parents=True)
    for tag_model in tag_data.tags:
        if tag_model.ai_analysis:
            save_tag_as_markdown(tag_model, topics_directory)

    # by user
    users_directory = save_path / "by_user"
    users_directory.mkdir(exist_ok=True, parents=True)
    for user_key, user_data in user_data.users.items():
        save_user_as_markdown(user_key=user_key,
                              user_data=user_data,
                              users_directory=users_directory)

    # by category/channel/thread
    by_server_directory = save_path / "by_server"
    for category_key, category_data in server_data.categories.items():
        save_category_as_markdown(category_data, by_server_directory)

    logger.info(f"Saved server data as markdown to {save_path}!")


