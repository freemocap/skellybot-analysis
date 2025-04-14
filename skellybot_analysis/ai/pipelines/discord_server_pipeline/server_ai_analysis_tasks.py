import asyncio
import logging

from skellybot_analysis.ai.pipelines.discord_server_pipeline.add_server_analysis_task import add_ai_analysis
from skellybot_analysis.models.data_models.server_data.server_data_model import ServerData
from skellybot_analysis.models.data_models.tag_models import TagManager
from skellybot_analysis.models.data_models.user_data_model import UserDataManager
from skellybot_analysis.models.prompt_models.text_analysis_prompt_model import TextAnalysisPromptModel
from skellybot_analysis.models.prompt_models.topic_article_writer_prompt_model import \
    WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT, \
    WikipediaStyleArticleWriterModel
from skellybot_analysis.models.prompt_models.user_profile_prompt_model import UserProfilePromptModel

logger = logging.getLogger(__name__)

async def ai_analyze_server_data(system_prompt_og: str, server_data: ServerData):
    system_prompt = system_prompt_og + (
        "\n You are currently reviewing the chat data from the server extracting the content "
        "of the conversations to provide a landscape of the topics that the students are discussing. "
        f"Provide your output in accordance to the provided JSON  schema.\n {TextAnalysisPromptModel.as_description_schema()}")
    analyzable_things = server_data.get_all_sub_objects(include_messages=False)
    ai_analysis_tasks = [add_ai_analysis(thing=thing,
                                         text_to_analyze=thing.as_text(),
                                         prompt_model=TextAnalysisPromptModel,
                                         system_prompt=system_prompt) for thing in analyzable_things]
    logger.info(f"Starting AI analysis tasks on {len(ai_analysis_tasks)} analyzable things.")
    await asyncio.gather(*ai_analysis_tasks)
    for thing in analyzable_things:
        if thing.ai_analysis is None:
            logger.error(f"Failed to analyze {thing.__class__.__name__}: {thing.name}")
    return server_data


async def ai_analyze_user_data(user_data: UserDataManager,
                               system_prompt_og: str) -> UserDataManager:
    user_ai_analysis_tasks = [add_ai_analysis(thing=user,
                                              text_to_analyze=user.as_ai_prompt_text(),
                                              prompt_model=UserProfilePromptModel,
                                              system_prompt=system_prompt_og) for user in user_data.users.values()]
    await asyncio.gather(*user_ai_analysis_tasks)
    for user in user_data.users.values():
        if user.ai_analysis is None:
            logger.error(f"Failed to analyze {user.__class__.__name__}: {user.name}")
    return user_data


async def ai_analyze_topic_tags(tag_manager: TagManager,
                                system_prompt_og: str,
                                min_tag_rank: int = 20
                                ) -> TagManager:
    system_prompt = system_prompt_og + f"\n\n{WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT}"
    tasks = []
    for tag in tag_manager.tags:
        if tag.link_count < min_tag_rank:
            logger.debug(f"Skipping tag {tag.name} due to low link count")
            continue
        logger.info(f"Analyzing tag {tag.name} with {len(tag.tagged_threads)} tagged threads")
        all_tagged_threads_str = "\n_____________________\n".join(
            [thread.ai_analysis.to_string() for thread in tag.tagged_threads])
        task_description = "You are generating an article on the following topic:\n\n{tag.name}\n\n Prioritize the content of the conversation threads that are relevant to this topic. Consider the context of the course as a whole! "
        user_input_text = (
            f"{task_description} \n\n You are generating an article on the following topic:"
            f"\n\n{tag.name}\n\n"
            f"_____________________\n"
            f"To assist you in writing an article on this topic, here are some summaries of conversation threads that are relevant to this topic:"
            f"\n\n{all_tagged_threads_str}\n\n"
            f"REMEMBER!{task_description}"
        )

        tasks.append(add_ai_analysis(thing=tag,
                                     text_to_analyze=user_input_text,
                                     system_prompt=system_prompt,
                                     prompt_model=WikipediaStyleArticleWriterModel))
    await asyncio.gather(*tasks)
    return tag_manager
