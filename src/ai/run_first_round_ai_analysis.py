import asyncio
import logging

from src.ai.get_embeddings_for_text import get_embedding_for_text
from src.ai.make_openai_json_mode_ai_request import make_openai_json_mode_ai_request
from src.ai.openai_constants import OPENAI_CLIENT, DEFAULT_LLM, MAX_TOKEN_LENGTH
from src.ai.prompt_stuff.truncate_text_to_max_token_length import truncate_string_to_max_tokens
from src.models.data_models.server_data.server_data_model import ServerData
from src.models.data_models.data_object_model import DataObjectModel
from src.models.data_models.server_data.server_data_sub_object_models import ChatThread
from src.models.text_analysis_prompt_model import TextAnalysisPromptModel, TagModel
from src.scrape_server.scrape_server import MINIMUM_THREAD_MESSAGE_COUNT

logger = logging.getLogger(__name__)




async def add_ai_analysis(thing: DataObjectModel,
                          system_prompt: str):
    print(f"Adding AI analysis to {thing.__class__.__name__}: {thing.name}")
    text_to_analyze = truncate_string_to_max_tokens(thing.as_text(),
                                                    max_tokens=int(MAX_TOKEN_LENGTH * .8),
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

    analyzable_things = server_data.get_all_things(include_messages=False)
    to_remove = []
    for thing in analyzable_things:
        if isinstance(thing, ChatThread):
            if not thing.messages or len(thing.messages) < MINIMUM_THREAD_MESSAGE_COUNT:
                to_remove.append(thing)
    for thing in to_remove:
        analyzable_things.remove(thing)
    ai_analysis_tasks = [add_ai_analysis(thing=thing,
                                         system_prompt=system_prompt) for thing in analyzable_things]

    logger.info(f"Starting AI analysis tasks on {len(ai_analysis_tasks)} analyzable things.")
    await asyncio.gather(*ai_analysis_tasks)
    logger.info(f"First round AI analysis completed! Analyzed {len(ai_analysis_tasks)} things.")


if __name__ == "__main__":
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data, server_data_json_path = get_server_data()

    asyncio.run(run_first_round_ai_analysis(server_data))

    print("Done!")
