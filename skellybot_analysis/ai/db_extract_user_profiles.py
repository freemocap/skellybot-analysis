import asyncio
import logging

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import MAX_TOKEN_LENGTH, DEFAULT_LLM, OPENAI_CLIENT
from skellybot_analysis.ai.db_analyze_server_data import get_context_system_prompt
from skellybot_analysis.models.server_db_models import UserThread, Thread
from skellybot_analysis.models.user_db_models import User, UserProfile
from skellybot_analysis.models.ai_analysis_db import ServerObjectAiAnalysis
from skellybot_analysis.models.prompt_models import TextAnalysisPromptModel
from skellybot_analysis.utilities.chunk_text_to_max_token_length import chunk_string_by_max_tokens
from skellybot_analysis.utilities.initialize_database import initialize_database_engine
from skellybot_analysis.utilities.load_env_variables import TARGET_SERVER_ID

logger = logging.getLogger(__name__)


async def db_extract_user_profiles(server_id: int, db_path: str | None = None) -> None:
    """Run AI analysis on server data stored in the SQLite database"""
    db_engine: Engine = initialize_database_engine(db_path=db_path)
    analysis_tasks = []
    with Session(db_engine) as session:
        # Get the server from the DB
        users = session.exec(select(User)).all()
        if not users:
            logger.error("No usersr found in database")
            return

        # Build the system prompt from context system prompts
        server_base_prompt = get_context_system_prompt(session=session,
                                                       server_id=server_id)

        logger.info(f"Analyzing {len(users)} users")
        for user in users:
            # Run analysis at the server level
            analysis_tasks.append(analyze_user(session=session,
                                               server_id=server_id,
                                               user=user,
                                               server_system_prompt=server_base_prompt
                                               )
                                  )

            logger.info(f"Starting AI analysis tasks on {len(analysis_tasks)} users.")
            await asyncio.gather(*analysis_tasks)

            logger.info("AI User analysis completed!")


async def analyze_user(
        session: Session,
        user: User,
        server_id: int,
        server_system_prompt: str) -> None:
    """
    Run AI analysis on a server object (server, category, or channel)
    and store the results in the ServerObjectAiAnalysis table.
    """
    # Get text content based on object type
    text_to_analyze = get_user_text(session=session,
                                      user=user,)
    if not text_to_analyze:
        logger.warning(f"No text content found for {user.name} ID: {user.id}")
        return

    # Enhance system prompt for analysis
    enhanced_system_prompt = ("You are currently reviewing the chat data from the server extracting the content "
                              "of the conversations to develop a profile of the human users based on their interactions with the bot in this server. "
                              f" Here is the System Prompt that was driving the bot's behavior during the conversation:\n"
                              f" BEGIN SYSTEM PROMPT\n\n\n"
                              f"{server_system_prompt}\n\n\n"
                              f"END SYSTEM PROMPT\n"
                              f"Here are the summaries and full-texts of the conversations this user had with the Bot in the server. "
                              " Please analyze the conversations and provide a summary of the user's profile. "
                              " Provide your output in accordance to the provided JSON schema."
                              f":\n\n"
                              )

    # Run AI analysis
    try:
        user_profile = await analyze_user_text(text_to_analyze, enhanced_system_prompt)

        # Store analysis in database
        store_user_profile_result(
            session=session,
            base_text=text_to_analyze,
            user_name=user.name,
            user_id=user.id,
            user_profile=user_profile,
        )

        logger.info(f"Successfully analyzed user {user.name} ID: {user.id}")
    except Exception as e:
        logger.error(f"Error analyzing user {user.name} ID: {user.id}: {e}")
        raise


def get_user_text(session: Session, user:User) -> str:
    """Get all the relevant text for this user from the db"""
    user_threads = session.exec(
        select(UserThread).where(Thread.user_id == user.id)
    ).all()
    if not user_threads:
        logger.warning(f"No threads found for user ID: {user.id}")
        return ""
    texts = []
    for user_thread in user_threads:
        analysis = session.exec(
            select(ServerObjectAiAnalysis).where(Thread.id == user_thread.thread_id)
        ).first()
        if analysis:
            texts.append(analysis.full_text)

    return "\n".join(texts)



async def analyze_user_text(text_to_analyze: str, system_prompt: str) -> UserProfile:
    """Run the AI analysis on the text content"""
    text_chunks = chunk_string_by_max_tokens(
        text_to_analyze,
        max_tokens=int(MAX_TOKEN_LENGTH * 0.8),
        llm_model=DEFAULT_LLM
    )

    analysis_result = None
    chunk_based_message = ""

    if len(text_chunks) > 1:
        logger.info(f"Text is too long, chunking into {len(text_chunks)} parts")
        system_prompt += ("\nThe text you are analyzing is too long to analyze in one go. "
                          "You will need to analyze it in chunks.")
        chunk_based_message = f"Here is chunk #1 out of {len(text_chunks)}:"

    for chunk_number, text_chunk in enumerate(text_chunks):
        modified_system_prompt = system_prompt + chunk_based_message

        analysis_result = await make_openai_json_mode_ai_request(
            client=OPENAI_CLIENT,
            system_prompt=modified_system_prompt,
            user_input=text_chunk,
            prompt_model=TextAnalysisPromptModel,
            llm_model=DEFAULT_LLM
        )

        # Update message for subsequent chunks
        if chunk_number < len(text_chunks) - 1:
            chunk_based_message = (
                f"Here is chunk #{chunk_number + 2} out of {len(text_chunks)}. "
                f"Here is the running AI analysis of the previous chunk(s):\n"
                f"{analysis_result.model_dump_json(indent=2)}\n\n"
                f"Use the previous results in conjunction with the new text to continue the analysis."
            )

    return analysis_result


def store_user_profile_result(
        session: Session,
        base_text:str,
        user_name:str,
        user_id:int,
        user_profile:UserProfile,
) -> None:
    """Store the analysis result in the ServerObjectAiAnalysis table"""
    # Check if analysis already exists
    existing = session.exec(
        select(ServerObjectAiAnalysis).where(ServerObjectAiAnalysis.user_id == user_id)
    ).first()

    if existing:
        # Update existing analysis
        existing.base_text = base_text

    else:
        # Create new analysis
        profile = UserProfile(

        )
        session.add(profile)

    session.commit()


if __name__ == "__main__":
    asyncio.run(db_extract_user_profiles(TARGET_SERVER_ID))
