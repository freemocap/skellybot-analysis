import asyncio
import logging

from src.ai.make_openai_json_mode_ai_request import make_openai_json_mode_ai_request
from src.ai.openai_constants import OPENAI_CLIENT, DEFAULT_LLM, MAX_TOKEN_LENGTH
from src.ai.prompt_stuff.truncate_text_to_max_token_length import truncate_string_to_max_tokens
from src.models.data_models.server_data.server_data_model import ServerData
from src.models.data_models.data_object_model import DataObjectModel
from src.models.data_models.server_data.server_data_sub_object_models import ChatThread
from src.models.data_models.server_data.user_data_model import UserData
from src.models.prompt_models.text_analysis_prompt_model import TextAnalysisPromptModel
from src.scrape_server.scrape_server import MINIMUM_THREAD_MESSAGE_COUNT

logger = logging.getLogger(__name__)




async def add_ai_analysis(thing: DataObjectModel,
                          text_to_analyze: str,
                          system_prompt: str):
    print(f"Adding AI analysis to {thing.__class__.__name__}: {thing.name}")
    text_to_analyze = truncate_string_to_max_tokens(text_to_analyze,
                                                    max_tokens=int(MAX_TOKEN_LENGTH * .9),
                                                    llm_model=DEFAULT_LLM)

    try:
        thing.ai_analysis = await make_openai_json_mode_ai_request(client=OPENAI_CLIENT,
                                                                   system_prompt=system_prompt,
                                                                   user_input=text_to_analyze,
                                                                   prompt_model=TextAnalysisPromptModel,
                                                                   llm_model=DEFAULT_LLM)

    except Exception as e:
        logger.error(f"Error adding AI analysis to {thing.__class__.__name__}: {thing.name}")
        logger.exception(e)
        logger.error(e)
        raise

    print(f"Completed AI analysis to {thing.__class__.__name__}: {thing.name}!")


async def run_first_round_ai_analysis(server_data: ServerData):
    system_prompt = server_data.server_system_prompt
    system_prompt += ("\n You are currently reviewing the chat data from the server extracting the content "
                      "of the conversations to provide a landscape of the topics that the students are discussing. "
                      f"Provide your output in accordance to the provided schema.\n {TextAnalysisPromptModel.as_description_schema()}")

    analyzable_things = server_data.get_all_sub_objects(include_messages=False,
                                                        include_users=False)


    ai_analysis_tasks = [add_ai_analysis(thing=thing,
                                        text_to_analyze=thing.as_text(),
                                         system_prompt=system_prompt) for thing in analyzable_things]

    logger.info(f"Starting AI analysis tasks on {len(ai_analysis_tasks)} analyzable things.")
    await asyncio.gather(*ai_analysis_tasks)

    # Analyze the users after the threads
    analyzable_users = list(server_data.get_users().values())
    user_ai_analysis_tasks = [add_ai_analysis(thing=user,
                                                text_to_analyze=user.as_text(),
                                                system_prompt=system_prompt) for user in analyzable_users]
    await asyncio.gather(*user_ai_analysis_tasks)
    for thing in analyzable_things:
        if thing.ai_analysis is None:
            logger.error(f"Failed to analyze {thing.__class__.__name__}: {thing.name}")
    logger.info(f"First round AI analysis completed! Analyzed {len(ai_analysis_tasks)} things.")


if __name__ == "__main__":
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data, server_data_json_path = get_server_data()

    asyncio.run(run_first_round_ai_analysis(server_data))

    print("Done!")
