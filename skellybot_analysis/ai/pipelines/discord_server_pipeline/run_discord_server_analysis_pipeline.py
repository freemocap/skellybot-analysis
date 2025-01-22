import asyncio
import logging

from skellybot_analysis.ai.pipelines.discord_server_pipeline.server_ai_analysis_tasks import ai_analyze_server_data, ai_analyze_user_data, ai_analyze_topic_tags
from skellybot_analysis.models.data_models.server_data.server_data_model import ServerData
from skellybot_analysis.models.data_models.tag_models import TagManager
from skellybot_analysis.models.data_models.user_data_model import UserDataManager

logger = logging.getLogger(__name__)


async def run_ai_analysis(server_data: ServerData) -> tuple[ServerData, UserDataManager, TagManager]:
    system_prompt_full = server_data.server_system_prompt
    system_prompt_og = system_prompt_full.split("CLASS BOT SERVER INSTRUCTIONS")[0]
    server_data = await ai_analyze_server_data(server_data=server_data,
                                               system_prompt_og=system_prompt_og)

    logger.success(f"Servers analyzed: {server_data.name}, server stats: {server_data.stats}")

    user_data = await ai_analyze_user_data(user_data=server_data.extract_user_data(),
                                           system_prompt_og=system_prompt_og)
    logger.success(f"Analyzed {len(list(user_data.users.keys()))} user(s), user stats: {user_data.stats}")

    tag_manager = TagManager.create(server_data=server_data, user_data=user_data)
    tag_manager = await ai_analyze_topic_tags(tag_manager=tag_manager,
                                              system_prompt_og=system_prompt_og)
    logger.success(f"Tags analyzed: {len(tag_manager.tags)}")

    return server_data, user_data, tag_manager


if __name__ == "__main__":
    from skellybot_analysis.utilities.get_most_recent_server_data import get_server_data

    server_data, server_data_json_path = get_server_data()

    asyncio.run(run_ai_analysis(server_data))

    print("Done!")
