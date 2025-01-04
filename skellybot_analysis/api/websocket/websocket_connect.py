import logging

from fastapi import APIRouter, WebSocket

from skellybot_analysis.api.websocket.websocket_server import SkellybotAnalysisWebsocketServer

logger = logging.getLogger(__name__)

skellybot_analysis_websocket_router = APIRouter()


@skellybot_analysis_websocket_router.websocket("/connect")
async def skellybot_analysis_websocket_server_connect(websocket: WebSocket):
    """
    Websocket endpoint for client connection to the server - handles image data streaming to frontend.
    """

    await websocket.accept()
    logger.success(f"SkellybotAnalysis Websocket connection established!")

    async with SkellybotAnalysisWebsocketServer(websocket=websocket) as runner:
        await runner.run()
    logger.info("Websocket closed")
