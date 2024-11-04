import asyncio
import logging

from openai import AsyncOpenAI
from src.ai.analyze_text import OPENAI_API_KEY, logger
from src.ai.get_embeddings_for_text import get_embedding_for_text
from src.ai.make_openai_json_mode_ai_request import make_openai_json_mode_ai_request
from src.ai.text_analysis_prompt_model import TextAnalysisPromptModel
from src.scrape_server.save_to_disk import save_server_data_to_json
from src.utilities.get_most_recent_server_data import get_most_recent_server_data

OPENAI_CLIENT = AsyncOpenAI(api_key=OPENAI_API_KEY)

DEFAULT_LLM = "gpt-4o-mini"

logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


class OpenaiJSONModeConfig:
    llm_model: str = DEFAULT_LLM


async def process_server_data():
    server_data, server_data_json_path = get_most_recent_server_data()
    system_prompt = server_data.server_system_prompt
    system_prompt += ("\n You are currently reviewing the chat data from the server extracting the content "
                      "of the conversations to provide a landscape of the topics that the students are discussing. "
                      f"Provide your output in accordance to the provided schema.\n {TextAnalysisPromptModel.as_description_schema()}")
    chat_threads = server_data.get_chat_threads()

    ai_analysis_tasks = []
    results = []
    logger.info(f"Fetched {len(chat_threads)} chat threads from the server data.")

    async def add_ai_analysis(thing):
        print(f"Adding AI analysis to {thing.__class__.__name__}: {thing.name}")
        try:
            thing.ai_analysis = await make_openai_json_mode_ai_request(client=OPENAI_CLIENT,
                                                                             system_prompt=system_prompt,
                                                                             user_input=thing.as_text(),
                                                                             prompt_model=TextAnalysisPromptModel,
                                                                             llm_model=DEFAULT_LLM,
                                                                             results_list=results)
            embedding_result = await get_embedding_for_text(thing.ai_analysis)
            thing.embeddings = {embedding_result.model: embedding_result[0].data[0].embedding}
        except Exception as e:
            logger.error(f"Error adding AI analysis to {thing.__class__.__name__}: {thing.name}")
            logger.error(e)
            return

        print(f"Added AI analysis to {thing.__class__.__name__}: {thing.name}!")

    for chat_thread in chat_threads:
        ai_analysis_tasks.append(add_ai_analysis(chat_thread))

    for channel in server_data.get_channels():
        ai_analysis_tasks.append(add_ai_analysis(channel))

    for category in server_data.get_categories():
        ai_analysis_tasks.append(add_ai_analysis(category))

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

    save_server_data_to_json(server_data=server_data, output_directory=server_data_json_path)
    logger.info(f"AI analysis tasks completed!")



if __name__ == "__main__":
    asyncio.run(process_server_data())

    print("Done!")
