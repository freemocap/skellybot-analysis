import asyncio
import json
import logging
from pathlib import Path

from src.ai.pipelines.run_first_round_ai_analysis import run_first_round_ai_analysis
from src.ai.pipelines.run_second_round_ai_analysis_openai import run_second_round_ai_analysis_openai
from src.scrape_server.save_to_disk import save_server_data_to_json
from src.scrape_server.save_to_markdown_directory import save_server_data_as_markdown_directory
from src.utilities.get_most_recent_server_data import get_server_data
from src.utilities.json_datatime_encoder import JSONDateTimeEncoder

logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

REPROCESS_EVERYTHING = True

async def process_server_data():
    server_data, server_data_json_path = get_server_data()
    output_directory = str(Path(server_data_json_path).parent)
    if server_data.ai_analysis is None or REPROCESS_EVERYTHING:
        await run_first_round_ai_analysis(server_data)
        save_server_data_to_json(server_data=server_data, output_directory=server_data_json_path)

    if server_data.graph_data is None or REPROCESS_EVERYTHING:
        await save_out_graph_data(server_data=server_data)
        save_server_data_to_json(server_data=server_data, output_directory=server_data_json_path)

    if server_data.get_tags()[0].ai_analysis is None or REPROCESS_EVERYTHING:
        await run_second_round_ai_analysis_openai(server_data)
        save_server_data_to_json(server_data=server_data, output_directory=server_data_json_path)

    save_server_data_as_markdown_directory(server_data=server_data, output_directory=output_directory)

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