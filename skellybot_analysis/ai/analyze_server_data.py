import asyncio
import json
import logging
from pathlib import Path

from skellybot_analysis.ai.embeddings_stuff.calculate_embeddings_and_tsne import create_embedding_and_tsne_clusters
from skellybot_analysis.ai.pipelines.discord_server_pipeline.run_discord_server_analysis_pipeline import run_ai_analysis
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

    await create_embedding_and_tsne_clusters(server_data)

    Path(server_data_json_path).write_text(server_data.model_dump_json(indent=2))
    save_server_data_as_markdown_directory(server_data=server_data,
                                           user_data=user_data,
                                           tag_data=tag_data,
                                           output_directory=output_directory)

    logger.info(f"AI analysis tasks completed!")



async def save_out_graph_data(server_data):
    await server_data.calculate_graph_data()
    json_output_path = Path(__file__).parent.parent.parent / 'docs' / 'datasets' / f'{server_data.name}_graph_data.json'
    with open(json_output_path, 'w', encoding='utf-8') as file:
        # file.write(json.dumps(graph_data.model_dump(),indent=2))
        json.dump(server_data.graph_data.model_dump(), file, indent=2, ensure_ascii=False, cls=JSONDateTimeEncoder)


if __name__ == "__main__":
    asyncio.run(process_server_data())

    print("Done!")
