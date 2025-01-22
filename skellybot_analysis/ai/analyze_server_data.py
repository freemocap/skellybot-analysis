import asyncio
import json
import logging
from pathlib import Path

from skellybot_analysis.ai.pipelines.discord_server_pipeline.run_discord_server_analysis_pipeline import run_ai_analysis
from skellybot_analysis.models.data_models.server_data.server_data_model import ServerData
from skellybot_analysis.models.data_models.tag_models import TagManager
from skellybot_analysis.models.data_models.user_data_model import UserDataManager
from skellybot_analysis.scrape_server.save_to_markdown_directory import save_server_data_as_markdown_directory
from skellybot_analysis.utilities.get_most_recent_server_data import get_server_data
from skellybot_analysis.utilities.json_datatime_encoder import JSONDateTimeEncoder

logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

REPROCESS_EVERYTHING = True


async def process_server_data():
    server_data, server_data_json_path = get_server_data()
    output_directory = str(Path(server_data_json_path).parent.parent)

    server_data, user_data, tag_data = await run_ai_analysis(server_data)

    await save_ai_analyzed_jsons(output_directory, server_data, server_data_json_path, tag_data,
                                 user_data)

    save_server_data_as_markdown_directory(server_data=server_data,
                                           user_data=user_data,
                                           tag_data=tag_data,
                                           output_directory=output_directory)

    logger.info(f"AI analysis tasks completed!")


async def save_ai_analyzed_jsons(output_directory: str,
                                 server_data: ServerData,
                                 server_data_json_path: str,
                                 tag_data: TagManager,
                                 user_data: UserDataManager):
    ai_output_directory = Path(output_directory) / 'ai_analysis'
    ai_output_directory.mkdir(parents=True, exist_ok=True)
    og_server_data_json_name = Path(server_data_json_path).name

    ai_analyzed_server_data_json_name = og_server_data_json_name.replace('.json', '_ai_analyzed.json')
    ai_analyzed_server_data_json_path = ai_output_directory / ai_analyzed_server_data_json_name
    ai_analyzed_server_data_json_path.write_text(server_data.model_dump_json(indent=2), encoding='utf-8')

    ai_analyzed_user_data_json_name = og_server_data_json_name.replace('server_data.json',
                                                                       '_ai_analyzed_user_data.json')
    ai_analyzed_user_data_json_path = ai_output_directory / ai_analyzed_user_data_json_name
    ai_analyzed_user_data_json_path.write_text(user_data.model_dump_json(indent=2), encoding='utf-8')

    ai_analyzed_tag_data_json_name = og_server_data_json_name.replace('server_data.json', '_ai_analyzed_tag_data.json')
    ai_analyzed_tag_data_json_path = ai_output_directory / ai_analyzed_tag_data_json_name
    ai_analyzed_tag_data_json_path.write_text(tag_data.stats.model_dump_json(indent=2), encoding='utf-8')


async def save_out_graph_data(server_data):
    await server_data.calculate_graph_data()
    json_output_path = Path(__file__).parent.parent.parent / 'docs' / 'datasets' / f'{server_data.name}_graph_data.json'
    with open(json_output_path, 'w', encoding='utf-8') as file:
        # file.write(json.dumps(graph_data.model_dump(),indent=2))
        json.dump(server_data.graph_data.model_dump(), file, indent=2, ensure_ascii=False, cls=JSONDateTimeEncoder)


if __name__ == "__main__":
    asyncio.run(process_server_data())

    print("Done!")
