import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

import skellybot_analysis
from skellybot_analysis.api.server.server_constants import APP_URL
from skellybot_analysis.system.files_and_folder_names import get_skellybot_analysis_data_folder_path

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.api(f"SkellybotAnalysis API starting (app: {app})...")
    logger.info(f"SkellybotAnalysis API base folder path: {get_skellybot_analysis_data_folder_path()}")
    Path(get_skellybot_analysis_data_folder_path()).mkdir(parents=True, exist_ok=True)


    logger.success(f"SkellybotAnalysis API (version:{skellybot_analysis.__version__}) started successfully 💀🤖✨")
    logger.api(f"SkellybotAnalysis API  running on: \n\t\t\tSwagger API docs - {APP_URL} \n\t\t\tTest UI: {APP_URL}/ui 👈[click to open backend UI in your browser]")

    # Let the app do its thing
    yield

    # Shutdown actions
    logger.api("SkellybotAnalysis API ending...")
    logger.success("SkellybotAnalysis API shutdown complete - Goodbye!👋")
