import logging
from pathlib import Path

from skellybot_analysis.models.dataframe_handler import DataframeHandler
from skellybot_analysis.system.logging_configuration.configure_logging import configure_logging
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

configure_logging()
logger = logging.getLogger(__name__)


def save_server_db_as_markdown_directory(dataframe_handler:DataframeHandler|None=None):
    """Save the server data from the SQL database as markdown files"""
    if dataframe_handler is None:
        db_path = get_most_recent_db_location()
        dataframe_handler = DataframeHandler.from_db_path(db_path=db_path)

    save_path = Path(dataframe_handler.db_path)
    logger.info(f"Saving server data as markdown to {save_path}")
    
    # Get all analyses
    if not dataframe_handler.thread_analyses:
        logger.warning("No analyses found in the database - nothing to save as markdown")
        return
    for analysis in dataframe_handler.thread_analyses:
        print(f"Saving analysis {analysis.context_route.names}  - {analysis.title_slug} analysis as markdown")
        analysis.save_as_markdown(base_folder=str(save_path))

    logger.info(f"Saved server data as markdown to {save_path}!")


if __name__ == "__main__":
    save_server_db_as_markdown_directory()