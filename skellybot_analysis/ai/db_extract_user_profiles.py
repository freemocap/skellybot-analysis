import asyncio
import logging

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import MAX_TOKEN_LENGTH, DEFAULT_LLM, OPENAI_CLIENT
from skellybot_analysis.ai.db_analyze_server_data import get_context_system_prompt
from skellybot_analysis.models.data_models.server_data.server_db_models import (
    Message, Channel, Thread, ServerObjectAiAnalysis, User
)
from skellybot_analysis.models.prompt_models.text_analysis_prompt_model import TextAnalysisPromptModel
from skellybot_analysis.models.prompt_models.user_profile_prompt_model import UserProfilePromptModel
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
        logger.warning(f"No text content found for {object_type} ID: {object_id}")
        return

    # Build context route
    context_route = f"{server_id}"
    context_route_names = f"{server_name}"
    if category_id is not None:
        context_route += f"/{category_id}"
        if category_name is None:
            raise ValueError("Category name is required when category_id is provided.")
        context_route_names += f"/{category_name}"
    if channel_id is not None:
        context_route += f"/{channel_id}"
        if channel_name is None:
            raise ValueError("Channel name is required when channel_id is provided.")
        context_route_names += f"/{channel_name}"
    if thread_id is not None:
        context_route += f"/{thread_id}"
        if thread_name is None:
            raise ValueError("Thread name is required when thread_id is provided.")
        context_route_names += f"/{thread_name}"

    # Enhance system prompt for analysis
    enhanced_system_prompt = ("You are currently reviewing the chat data from the server extracting the content "
                              "of the conversations to provide a landscape of the topics that are being discussed. "
                              f"Provide your output in accordance to the provided JSON schema. Here is the System Prompt that was driving the bot's behavior during the conversation:\n"
                              f" BEGIN SYSTEM PROMPT\n\n\n"
                              f"{system_prompt}\n\n\n"
                              f"END SYSTEM PROMPT\n"
                              f"Here is the text to analyze:\n\n"
                              )

    # Run AI analysis
    try:
        analysis_result = await analyze_text(text_to_analyze, enhanced_system_prompt)

        # Store analysis in database
        store_analysis_result(
            session=session,
            context_route=context_route,
            context_route_names=context_route_names,
            server_id=server_id,
            server_name=server_name,

            category_id=category_id,
            category_name=category_name,

            channel_id=channel_id,
            channel_name=channel_name,

            thread_id=thread_id,
            thread_name=thread_name,
            analysis_result=analysis_result,
            base_text=text_to_analyze
        )

        logger.info(f"Successfully analyzed {object_type} ID: {object_id}")
    except Exception as e:
        logger.error(f"Error analyzing {object_type} ID: {object_id}: {str(e)}")
        raise


def get_user_text(session: Session, user:User) -> str:
    """Get all the relevant text for this user from the db"""
    user_threads = session.exec(
        select(Thread).where(Thread.user_id == user.id)
    ).all()


async def analyze_user_text(text_to_analyze: str, system_prompt: str) -> UserProfilePromptModel:
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
        context_route: str,
        context_route_names: str,
        server_id: int,
        server_name: str,
        base_text: str,
        analysis_result: TextAnalysisPromptModel,
        category_id: int | None = None,
        category_name: str | None = None,

        channel_id: int | None = None,
        channel_name: str | None = None,
        thread_id: int | None = None,
        thread_name: str | None = None) -> None:
    """Store the analysis result in the ServerObjectAiAnalysis table"""
    # Check if analysis already exists
    existing = session.exec(
        select(ServerObjectAiAnalysis).where(ServerObjectAiAnalysis.context_route == context_route)
    ).first()

    if existing:
        # Update existing analysis
        existing.base_text = base_text
        existing.context_route_names = context_route_names
        existing.server_name = server_name
        existing.category_name = category_name
        existing.channel_name = channel_name
        existing.thread_name = thread_name
        existing.title_slug = analysis_result.title_slug
        existing.extremely_short_summary = analysis_result.extremely_short_summary
        existing.very_short_summary = analysis_result.very_short_summary
        existing.short_summary = analysis_result.short_summary
        existing.highlights = analysis_result.highlights if isinstance(analysis_result.highlights, str) else "\n".join(
            analysis_result.highlights)
        existing.detailed_summary = analysis_result.detailed_summary
        existing.tags = analysis_result.tags
    else:
        # Create new analysis
        analysis = ServerObjectAiAnalysis(

            context_route=context_route,
            context_route_names=context_route_names,

            server_id=server_id,
            server_name=server_name,

            category_id=category_id,
            category_name=category_name,

            channel_id=channel_id,
            channel_name=channel_name,

            thread_id=thread_id,
            thread_name=thread_name,

            base_text=base_text,
            title_slug=analysis_result.title_slug,
            extremely_short_summary=analysis_result.extremely_short_summary,
            very_short_summary=analysis_result.very_short_summary,
            short_summary=analysis_result.short_summary,
            highlights=analysis_result.highlights if isinstance(analysis_result.highlights, str) else "\n".join(
                analysis_result.highlights),
            detailed_summary=analysis_result.detailed_summary,
            tags=analysis_result.tags
        )
        session.add(analysis)

    session.commit()


if __name__ == "__main__":
    asyncio.run(db_analyze_user_data(TARGET_SERVER_ID))
