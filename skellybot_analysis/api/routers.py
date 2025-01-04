

from skellybot_analysis.api.http.app.health import health_router
from skellybot_analysis.api.http.app.shutdown import app_shutdown_router
from skellybot_analysis.api.http.app.state import state_router
from skellybot_analysis.api.http.ui.ui_router import ui_router
from skellybot_analysis.api.websocket.websocket_connect import skellybot_analysis_websocket_router

OTHER_ROUTERS = {}

SKELLYBOT_ANALYSIS_ROUTERS = {
    "/ui": {
        "ui": ui_router
    },
    "/app": {
        "health": health_router,
        "state": state_router,
        "shutdown": app_shutdown_router
    },
    "/websocket": {
        "connect": skellybot_analysis_websocket_router
    },

    **OTHER_ROUTERS
}