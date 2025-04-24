import asyncio
import logging
from copy import deepcopy

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import MAX_TOKEN_LENGTH, DEFAULT_LLM, OPENAI_CLIENT
from skellybot_analysis.models.ai_analysis_db import ServerObjectAiAnalysis, TopicArea
from skellybot_analysis.models.context_route import ContextRoute
from skellybot_analysis.models.prompt_models import TextAnalysisPromptModel
from skellybot_analysis.models.server_db_models import  Thread, ContextSystemPrompt, Message
from skellybot_analysis.utilities.initialize_database import initialize_database_engine

MIN_MESSAGE_LIMIT = 4

logger = logging.getLogger(__name__)


async def db_analyze_server_threads(db_path: str | None = None) -> None:
    """Run AI analysis on server data stored in the SQLite database"""
    db_engine: Engine = initialize_database_engine(db_path=db_path)
    analysis_tasks = []
    context_routes = []
    thread_ids = []
    with Session(db_engine) as session:

        # Run analysis on threads
        threads = session.exec(select(Thread)).all()
        logger.info(f"Analyzing {len(threads)} threads from server: {threads[0].server_name} ")
        for thread in threads:
            analysis_tasks.append(asyncio.create_task(analyze_thread(session=session,
                                                                     context_route=ContextRoute(
                                                                            server_id=thread.server_id,
                                                                            server_name=thread.server_name,
                                                                            category_id=thread.category_id,
                                                                            category_name=thread.category_name,
                                                                            channel_id=thread.channel_id,
                                                                            channel_name=thread.channel_name,
                                                                     ),
                                                                     thread_id=thread.id,
                                                                     thread_name=thread.name,
                                                                     ))
                                  )

        logger.info(f"Starting AI analysis tasks on {len(analysis_tasks)} objects.")
        results = await asyncio.gather(*analysis_tasks)
        analysis_results = {route: result for route, result in zip(context_routes, results)}
        store_analysis_results(analysis_results=analysis_results,
                               session=session)
        logger.info("AI analysis completed!")


def get_context_system_prompt(session: Session, context_route: ContextRoute) -> str:
    """Get the system prompt for a server from the ContextSystemPrompt table"""

    prompt_obj = session.exec(
        select(ContextSystemPrompt).where(ContextSystemPrompt.id == context_route.hash_id)
    ).first()

    if prompt_obj and prompt_obj.system_prompt:
        return prompt_obj.system_prompt
    return ""


async def analyze_thread(session: Session,
                         context_route: ContextRoute,
                         thread_id: int,
                         thread_name: str,
                         ) -> tuple[int, str, str, str, TextAnalysisPromptModel] | None:
    """
    Run AI analysis on a server object (server, category, or channel)
    and store the results in the ServerObjectAiAnalysis table.
    """
    channel_prompt = get_context_system_prompt(session=session,
                                               context_route=context_route)
    if not channel_prompt:
        raise ValueError(f"WARNING - No system prompt found for {context_route.names} with hash_id {context_route.hash_id}.")

    # Get text content based on object type
    thread_text_to_analyze = get_thread_text(session=session,
                                             thread_id=thread_id,
                                             )
    if len(thread_text_to_analyze.split(" ")) > MAX_TOKEN_LENGTH:
        logger.warning(
            f"Thread text is too longer than {MAX_TOKEN_LENGTH} tokens, truncating to {MAX_TOKEN_LENGTH} tokens.")
        thread_text_to_analyze = " ".join(thread_text_to_analyze.split(" ")[:MAX_TOKEN_LENGTH])
    if not thread_text_to_analyze:
        logger.warning(f"No text content found for thread `{thread_id}`: {context_route.names}, skipping analysis.")
        return None

    # Enhance system prompt for analysis
    analysis_prompt = (
        f"You are currently reviewing the chat data from the {context_route.server_name} Discord server extracting the content "
        f"of the conversations to provide a landscape of the topics that are being discussed. \n\n"
        f"You are currently analyzing the text of a chat thread which occurred at this location in the server:\n\n"
        f"{context_route.as_formatted_text}\n\n"
        f" Here is the System Prompt that was driving the bot's behavior during the conversation:\n\n"
        f" BEGIN SYSTEM PROMPT\n\n\n"
        f"{channel_prompt}\n\n\n"
        f"END SYSTEM PROMPT\n"
        f"Here is the text to analyze:\n\n"
        f"BEGIN TEXT TO ANALYZE\n\n"
        f"{thread_text_to_analyze}\n\n"
        f"END TEXT TO ANALYZE\n"
        f"Carefully consider the content of this conversation in order to provide the output prescribed by the provided JSON schema."
    )

    # Run AI analysis
    try:
        result = await make_openai_json_mode_ai_request(client=OPENAI_CLIENT,
                                                        system_prompt=analysis_prompt,
                                                        prompt_model=TextAnalysisPromptModel,
                                                        llm_model=DEFAULT_LLM
                                                        )
        return thread_id, thread_name, thread_text_to_analyze, analysis_prompt, result
    except Exception as e:
        logger.error(f"Error analyzing {context_route.names}: {e}")
        raise


def store_analysis_results(analysis_results: dict[ContextRoute, tuple[int, str, str, str, TextAnalysisPromptModel]],
                           session: Session) -> None:
    """Store the analysis results in the database"""
    stored = 0
    try:
        for route, text_result in analysis_results.items():
            thread_id, thread_name, analyzed_text, analysis_prompt, analysis_result = text_result
            # Store analysis in database
            if not analysis_result:
                logger.warning(f"No analysis result for {route.names}, skipping storage.")
                continue
            ServerObjectAiAnalysis.get_create_or_update(
                db_id=route.hash_id,
                session=session,
                flush=True,
                context_route_ids=route.ids,
                context_route_names=route.names,
                server_id=route.server_id,
                server_name=route.server_name,
                category_id=route.category_id,
                category_name=route.category_name,
                channel_id=route.channel_id,
                channel_name=route.channel_name,
                thread_id=thread_id,
                thread_name=thread_name,
                base_text=analyzed_text,
                analysis_prompt=analysis_prompt,
                title_slug=analysis_result.title_slug,
                extremely_short_summary=analysis_result.extremely_short_summary,
                very_short_summary=analysis_result.very_short_summary,
                short_summary=analysis_result.short_summary,
                highlights=analysis_result.highlights if isinstance(analysis_result.highlights, str) else "\n".join(
                    analysis_result.highlights),
                detailed_summary=analysis_result.detailed_summary,
                topic_areas=[TopicArea.from_prompt_model(topic) for topic in analysis_result.topic_areas]
            )
            session.commit()
            stored += 1

        logger.info(f"Analysis results stored successfully - stored {stored} results out of {len(analysis_results)}.")
    except Exception as e:
        logger.error(f"Error storing analysis results: {e}")
        session.rollback()




def get_thread_text(session: Session, thread_id: int) -> str:
    # Get all messages in the thread
    thread = session.exec(select(Thread).where(Thread.id == thread_id)).first()

    # Format messages as text
    thread_texts = []
    messages = session.exec(select(Message).where(Message.thread_id == thread_id)).all()
    # ensure sorting by timestamp
    messages.sort(key=lambda x: x.timestamp)
    if not messages:
        logger.warning(f"Thread {thread.name} (id: {thread.id}) has no messages, skipping analysis.")
        return ""
    if thread.name == ".":
        if len(messages) < MIN_MESSAGE_LIMIT:
            logger.warning(f"Thread {thread.name} has less than {MIN_MESSAGE_LIMIT} messages, skipping analysis.")
            return ""
    thread_text = f"Thread: {thread.name} (id: {thread.id})\n\nurl: {messages[0].jump_url}\n\n"
    for msg in messages:
        thread_text += f"{msg.as_full_text(with_names=True)}\n\n"
    thread_text += "\n\n_______________\n\n"
    thread_texts.append(thread_text)
    return "\n".join(thread_texts)


if __name__ == "__main__":
    asyncio.run(db_analyze_server_threads())
