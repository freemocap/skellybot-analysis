import logging
from pathlib import Path

from sqlmodel import Session, select

from skellybot_analysis.models.db_models.db_ai_analysis_models import ServerObjectAiAnalysis
from skellybot_analysis.system.logging_configuration.configure_logging import configure_logging
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location
from skellybot_analysis.utilities.initialize_database import initialize_database_engine

configure_logging()
logger = logging.getLogger(__name__)


def save_server_db_as_markdown_directory(db_path: str | None = None):
    """Save the server data from the SQL database as markdown files"""
    if db_path is None:
        db_path = get_most_recent_db_location()
    
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    db_engine = initialize_database_engine(str(db_path))
    
    save_path = db_path.parent
    logger.info(f"Saving server data as markdown to {save_path}")
    
    with Session(db_engine) as session:
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