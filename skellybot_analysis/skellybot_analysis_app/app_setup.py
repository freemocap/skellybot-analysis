import logging

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse

import skellybot_analysis
from skellybot_analysis.api.routers import SKELLYBOT_ANALYSIS_ROUTERS

logger = logging.getLogger(__name__)


def register_routes(app: FastAPI):
    @app.get("/")
    async def read_root():
        return RedirectResponse("/docs")

    # @app.get('/favicon.ico', include_in_schema=False)
    # async def favicon():
    #     return FileResponse(SKELLYCAM_FAVICON_ICO_PATH)

    for prefix, routers in SKELLYBOT_ANALYSIS_ROUTERS.items():
        for name, router in routers.items():
            logger.api(f"Registering route: `{prefix}/{name}`")
            app.include_router(router, prefix=prefix)


def customize_swagger_ui(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Welcome to the SkellyBot Analysis API 💀🤖✨",
            version=skellybot_analysis.__version__,
            description=f"The FastAPI/Uvicorn/Swagger Backend UI for SkellybotAnalysis: {skellybot_analysis.__description__}",
            routes=app.routes,
        )

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
