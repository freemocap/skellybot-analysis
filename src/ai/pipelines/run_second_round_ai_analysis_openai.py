import asyncio
import json
import logging
from pprint import pprint

from src.ai.openai_constants import OPENAI_CLIENT
from src.models.prompt_models.topic_article_writer_prompt_model import WikipediaStyleArticleWriterModel, \
    WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT
from src.models.data_models.server_data.server_data_model import ServerData

logger = logging.getLogger(__name__)

MIN_TAG_RANK = 2 # Minimum number of threads a tag must be present in to be considered for analysis

async def run_second_round_ai_analysis_openai(server_data: ServerData):
    system_prompt_og = server_data.server_system_prompt
    system_prompt = system_prompt_og.split("CLASS BOT SERVER INSTRUCTIONS")[0]

    system_prompt += f"\n\n{WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT}"

    all_threads = server_data.get_chat_threads()
    tasks = []
    analyzed_tags = []
    threads_by_tag = {}
    for tag in server_data.get_tags():
        if tag.link_count < MIN_TAG_RANK:
            logger.info(f"Skipping tag {tag.name} due to low link count")
            continue
        analyzed_tags.append(tag)
        threads_with_tag = []
        for thread in all_threads:
            if tag.name in thread.ai_analysis.tags_list:
                threads_with_tag.append(thread)
        threads_by_tag[tag.name] = threads_with_tag
        all_tagged_threads_str = "\n_____________________\n".join([thread.ai_analysis.to_string() for thread in threads_with_tag])
        task_description = WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT
        user_input_prompt = (
            f"{task_description} \n\n The following are summaries of threads that are relevant to this topic:"
            f"\n\n{all_tagged_threads_str}\n\n"
            f" REMEMBER! {task_description}")

        tasks.append( OPENAI_CLIENT.beta.chat.completions.parse(
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
            response_format=WikipediaStyleArticleWriterModel
        )
        )
    outputs = await asyncio.gather(*tasks)
    for tag, output in zip(analyzed_tags, outputs):
        tag.ai_analysis = WikipediaStyleArticleWriterModel(**json.loads(output.choices[0].message.content))
        for thread in threads_by_tag[tag.name]:
            tag.tagged_threads.append(thread.ai_analysis.title)
        print(tag.ai_analysis.as_text())
    return server_data


if __name__ == "__main__":
    from src.utilities.get_most_recent_server_data import get_server_data

    server_data_, server_data_json_path = get_server_data()

    asyncio.run(run_second_round_ai_analysis_openai(server_data_))
    print("Done!")