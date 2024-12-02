import asyncio
import json
import logging
from pprint import pprint

from src.ai.openai_constants import OPENAI_CLIENT
from src.models.prompt_models.topic_article_writer_prompt_model import WikipediaArticleWriterModel, \
    WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT
from src.models.data_models.server_data.server_data_model import ServerData

logger = logging.getLogger(__name__)

MIN_TAG_RANK = 1 # Minimum number of threads a tag must be present in to be considered for analysis

async def run_second_round_ai_analysis(server_data: ServerData):
    system_prompt_og = server_data.server_system_prompt
    system_prompt = system_prompt_og.split("CLASS BOT SERVER INSTRUCTIONS")[0]

    system_prompt += f"\n\n{WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT}"

    all_threads = server_data.get_chat_threads()
    tasks = []
    for tag in server_data.get_tags():
        if tag.link_count < MIN_TAG_RANK:
            logger.info(f"Skipping tag {tag.name} due to low link count")
            continue
        threads_for_tag = [thread for thread in all_threads if tag in thread.tags]
        thread_analysis_string = ""
        for thread in threads_for_tag:
            thread_analysis_string += thread.ai_analysis.to_string() + "\n______________\n"
        task_description = ("Your task is to generate an expansive report for the topic {tag} based on the information "
                            "covered in the included chat thread summaries. ")
        user_input_prompt = (
            f"{task_description} \n\n The following are the analyses and summaries of threads that are relevant to this topic:"
            f"\n\n{thread_analysis_string}\n\n REMEMBER! {task_description}")

        tasks.append(OPENAI_CLIENT.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_input_prompt
                }
            ],
            response_format=WikipediaArticleWriterModel
        ))

    outputs = await asyncio.gather(*tasks)
    for tag, output in zip(server_data.get_tags(), outputs):
        tag.ai_analysis = WikipediaArticleWriterModel(**json.loads(output.choices[0].message.content))
        pprint(tag.ai_analysis.model_dump_json(indent=2))
    return server_data


if __name__ == "__main__":
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data_, server_data_json_path = get_server_data()

    asyncio.run(run_second_round_ai_analysis(server_data_))
    print("Done!")
