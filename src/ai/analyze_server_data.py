import asyncio
import logging
from pathlib import Path

from src.ai.run_first_round_ai_analysis import run_first_round_ai_analysis
from src.scrape_server.save_to_disk import save_server_data_to_json
from src.scrape_server.save_to_markdown_directory import save_as_markdown_directory
from src.utilities.get_most_recent_server_data import get_server_data

logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("openai").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)

logger = logging.getLogger(__name__)





async def process_server_data():
    server_data, server_data_json_path = get_server_data()

    await run_first_round_ai_analysis(server_data)

    await server_data.calculate_graph_data()

    save_server_data_to_json(server_data=server_data, output_directory=server_data_json_path)
    save_as_markdown_directory(server_data=server_data, output_directory=str(Path(server_data_json_path).parent))

    logger.info(f"AI analysis tasks completed!")


if __name__ == "__main__":
    asyncio.run(process_server_data())

    print("Done!")