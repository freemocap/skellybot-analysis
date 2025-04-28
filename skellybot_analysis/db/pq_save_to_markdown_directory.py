import logging
from pathlib import Path

from sqlmodel import select

from skellybot_analysis.db.sql_db.sql_db_models import ServerObjectAiAnalysis
from skellybot_analysis.db.sql_db.db_utilities import get_db_session
from skellybot_analysis.system.logging_configuration.configure_logging import configure_logging
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

configure_logging()
logger = logging.getLogger(__name__)


def save_server_db_as_markdown_directory(db_path: str | None = None):
    """Save the server data from the SQL database as markdown files"""
    if db_path is None:
        db_path = get_most_recent_db_location()

    save_path = Path(db_path).parent
    logger.info(f"Saving server data as markdown to {save_path}")
    
    with get_db_session(db_path=db_path) as session:
        # Get all analyses
        analyses = session.exec(select(ServerObjectAiAnalysis)).all()
        if not analyses:
            logger.warning("No analyses found in the database - nothing to save as markdown")
            return
        for analysis in analyses:
            print(f"Saving analysis {analysis.context_route_names} analysis as markdown")
            analysis.save_as_markdown(base_folder=str(save_path))

    logger.info(f"Saved server data as markdown to {save_path}!")


if __name__ == "__main__":
    save_server_db_as_markdown_directory()