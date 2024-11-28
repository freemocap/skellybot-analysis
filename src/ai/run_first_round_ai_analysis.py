import asyncio
import logging

from src.ai.openai_constants import OPENAI_CLIENT, DEFAULT_LLM, MAX_TOKEN_LENGTH
from src.ai.get_embeddings_for_text import get_embedding_for_text
from src.ai.make_openai_json_mode_ai_request import make_openai_json_mode_ai_request
from src.ai.prompt_stuff.truncate_text_to_max_token_length import truncate_string_to_max_tokens
from src.models.server_data_model import ServerData
from src.models.text_analysis_prompt_model import TextAnalysisPromptModel

logger = logging.getLogger(__name__)
async def add_embedding_vector(thing, text_to_analyze: str):
    embedding_result = await get_embedding_for_text(client=OPENAI_CLIENT,
                                                    text_to_embed=text_to_analyze)
    thing.embedding = embedding_result

async def add_ai_analysis(thing,
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
        await add_embedding_vector(thing=thing, text_to_analyze=text_to_analyze)



    except Exception as e:
        logger.error(f"Error adding AI analysis to {thing.__class__.__name__}: {thing.name}")
        logger.exception(e)
        logger.error(e)
        return

    print(f"Completed AI analysis to {thing.__class__.__name__}: {thing.name}!")



async def run_first_round_ai_analysis(server_data: ServerData):
    system_prompt = server_data.server_system_prompt
    system_prompt += ("\n You are currently reviewing the chat data from the server extracting the content "
                      "of the conversations to provide a landscape of the topics that the students are discussing. "
                      f"Provide your output in accordance to the provided schema.\n {TextAnalysisPromptModel.as_description_schema()}")

    chat_threads = server_data.get_chat_threads()
    ai_analysis_tasks = []
    logger.info(f"Fetched {len(chat_threads)} chat threads from the server data.")
    ai_analysis_tasks.append(add_ai_analysis(thing=server_data,
                                             system_prompt=system_prompt))
    for user_data in server_data.extract_user_data().values():
        ai_analysis_tasks.append(add_ai_analysis(thing=user_data,
                                                 system_prompt=system_prompt))
    for category in server_data.get_categories():
        ai_analysis_tasks.append(add_ai_analysis(thing=category,
                                                 system_prompt=system_prompt))
    for channel in server_data.get_channels():
        ai_analysis_tasks.append(add_ai_analysis(thing=channel,
                                                 system_prompt=system_prompt))
    for chat_thread in chat_threads:
        if len(chat_thread.messages) < 3:
            continue

        ai_analysis_tasks.append(add_ai_analysis(thing=chat_thread,
                                                 system_prompt=system_prompt))
        # for message in chat_thread.messages:
        #     if len(message.content) > 20:
        #         ai_analysis_tasks.append(add_embedding_vector(thing=message,
        #                                                       text_to_analyze=message.content))
    logger.info(f"Starting AI analysis tasks on {len(ai_analysis_tasks)} chat threads...")
    await asyncio.gather(*ai_analysis_tasks)
    for chat in server_data.get_chat_threads():
        if chat.ai_analysis:
            logger.debug(f"Chat thread: {chat.as_text()}")
            logger.debug(f"AI Analysis: {chat.ai_analysis}")
            logger.debug("")
    for channel in server_data.get_channels():
        if channel.ai_analysis:
            logger.info(f"Channel: {channel.as_text()}")
            logger.info(f"AI Analysis: {channel.ai_analysis}")
            logger.info("")
    for category in server_data.get_categories():
        if category.ai_analysis:
            logger.success(f"Category: {category.as_text()}")
            logger.success(f"AI Analysis: {category.ai_analysis}")
            logger.success("")


if __name__ == "__main__":
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data, server_data_json_path = get_server_data()

    asyncio.run(run_first_round_ai_analysis(server_data))

    print("Done!")