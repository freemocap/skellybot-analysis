import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
ingesters_router = APIRouter()

@ingesters_router.get("/ingesters/pdf", summary="Hello👋")
def pdf_ingestion_endpoint():
    """
    A simple endpoint to greet the user of the SkellyBot Analysis API.

    This can be used as a sanity check to ensure the API is responding.
    """

    logger.api("Hello requested! Deploying Hello!")
    return HELLO_FROM_SKELLYBOT_ANALYSIS_BACKEND_MESSAGE


# @connect_cameras_router.post(
#     "/connect/apply",
#
#     summary="Connect/Update specified cameras and apply provided configuration settings",
# )
# def cameras_apply_config_route(
#         request: CameraConfigs = Body(..., examples=[default_camera_configs_factory()])
# ):
#     logger.api("Received `skellycam/cameras/connect/apply` POST request...")
#     try:
#         get_skellycam_app_controller().connect_to_cameras(camera_configs=request)
#         logger.api("`skellycam/cameras/connect/apply` POST request handled successfully.")
#     except Exception as e:
#         logger.error(f"Error when processing `/connect` request: {type(e).__name__} - {e}")
#         logger.exception(e)
#
#
# @connect_cameras_router.get(
#     "/connect/detect",
#     summary="Detect and connect to all available cameras with default settings",
# )
# def detect_and_connect_to_cameras_route():
#     logger.api("Received `skellycam/cameras/connect` GET request...")
#     try:
#         get_skellycam_app_controller().connect_to_cameras()
#         logger.api("`skellycam/cameras/connect` GET request handled successfully.")
#     except Exception as e:
#         logger.error(f"Failed to detect available cameras: {type(e).__name__} - {e}")
#         logger.exception(e)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(ingesters_router, host="localhost", port=8000)