from sqlalchemy import create_engine
from sqlmodel import Session, select

from skellybot_analysis.old_db.sql_db.sql_db_models.db_server_models import Message, Thread, User
from skellybot_analysis.utilities.get_most_recent_db_location import get_most_recent_db_location

import  logging
logger = logging.getLogger(__name__)

async def print_server_db_stats(db_path: str|None=None):
    """Validate that data was properly saved to the database"""
    if db_path is None:
        db_path = get_most_recent_db_location()

    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    with Session(engine) as session:
        thread_count = session.query(Thread).count()
        message_count = session.query(Message).count()
        user_count = session.query(User).count()-2 # subtract 2 users, bot + me

        messages = session.exec(select(Message)).all()
        if not messages:
            raise ValueError("No messages found in the database")
        total_word_count = 0
        bot_word_count = 0
        human_word_count = 0
        for message in messages:
            total_word_count += len(message.content.split())
            if message.is_bot:
                bot_word_count += len(message.content.split())
            else:
                human_word_count += len(message.content.split())
        logger.info(f"Database validation results:")
        logger.info(f"  - Threads: {thread_count}")
        logger.info(f"  - Messages: {message_count}")
        logger.info(f"  - Users: {user_count}")
        logger.info(f"Total word count: {total_word_count:,}")
        logger.info(f"Bot word count: {bot_word_count:,}")
        logger.info(f"Human word count: {human_word_count:,}")
        logger.info(f"Mean word count per user: {total_word_count / user_count-2 if user_count > 0 else 0:,}") #subtract 2 users, bot + me




if __name__ == "__main__":
    import asyncio
    asyncio.run(print_server_db_stats())

