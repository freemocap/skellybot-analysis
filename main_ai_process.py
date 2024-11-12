import asyncio
import logging

from src.ai.analyze_server_data import process_server_data



logger = logging.getLogger(__name__)


if __name__ == "__main__":
    asyncio.run(process_server_data())

    print("Done!")
