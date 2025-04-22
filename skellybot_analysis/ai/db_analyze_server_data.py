import asyncio
import logging
import uuid

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import MAX_TOKEN_LENGTH, DEFAULT_LLM, OPENAI_CLIENT
from skellybot_analysis.models.data_models.server_db_models import Server, Category, Channel, Thread, \
    ContextSystemPrompt, Message
from skellybot_analysis.models.data_models.user_db_models import ServerObjectAiAnalysis
from skellybot_analysis.models.prompt_models.text_analysis_prompt_model import TextAnalysisPromptModel
from skellybot_analysis.utilities.chunk_text_to_max_token_length import chunk_string_by_max_tokens
from skellybot_analysis.utilities.initialize_database import initialize_database_engine

MIN_MESSAGE_LIMIT = 4

logger = logging.getLogger(__name__)


async def db_analyze_server_data(db_path: str | None = None) -> None:
    """Run AI analysis on server data stored in the SQLite database"""
    db_engine: Engine = initialize_database_engine(db_path=db_path)
    analysis_tasks = []
    with Session(db_engine) as session:
        # Get the server from the DB
        server = session.exec(select(Server)).first()
        if not server:
            logger.error("No server found in database")
            return

        logger.info(f"Analyzing server: {server.name} (ID: {server.id})")

        # Build the system prompt from context system prompts
        server_system_prompt = get_context_system_prompt(session=session,
                                                         server_id=server.id)

        # Run analysis at the server level
        analysis_tasks.append(analyze_object(session=session,
                                             server_id=server.id,
                                             server_name=server.name,
                                             object_id=server.id,
                                             object_name=server.name,
                                             object_type="server",
                                             system_prompt=server_system_prompt
                                             )
                              )
        # Run analysis on categories
        categories = session.exec(select(Category).where(Category.server_id == server.id)).all()
        logger.info(f"Analyzing {len(categories)} categories")

        for category in categories:
            logger.info(f"Analyzing category: {category.name} (ID: {category.id})")
            category_prompt = get_context_system_prompt(session=session,
                                                        server_id=server.id,
                                                        category_id=category.id)
            analysis_tasks.append(
                analyze_object(
                    session=session,
                    server_id=server.id,
                    server_name=server.name,
                    object_id=category.id,
                    object_name=category.name,
                    object_type="category",
                    category_id=category.id,
                    category_name=category.name,
                    system_prompt=category_prompt
                )
            )

        # Run analysis on channels
        channels = session.exec(select(Channel).where(Channel.server_id == server.id)).all()
        logger.info(f"Analyzing {len(channels)} channels")

        for channel in channels:
            logger.info(f"Analyzing channel: {channel.name} (ID: {channel.id})")
            channel_prompt = get_context_system_prompt(session=session,
                                                       server_id=server.id,
                                                       category_id=channel.category_id,
                                                       channel_id=channel.id)
            analysis_tasks.append(
                analyze_object(
                    session=session,
                    server_id=server.id,
                    server_name=server.name,
                    object_id=channel.id,
                    object_name=channel.name,
                    object_type="channel",
                    category_id=channel.category_id,
                    category_name=channel.category_name,
                    channel_id=channel.id,
                    channel_name=channel.name,
                    system_prompt=channel_prompt
                )
            )

        # Run analysis on threads
        threads = session.exec(select(Thread).join(Channel).where(Channel.server_id == server.id)).all()
        logger.info(f"Analyzing {len(threads)} threads")
        for thread in threads:
            logger.info(f"Analyzing thread: {thread.name} (ID: {thread.id})")
            channel = session.exec(select(Channel).where(Channel.id == thread.channel_id)).first()
            analysis_tasks.append(
                analyze_object(
                    session=session,
                    server_id=server.id,
                    server_name=server.name,
                    object_id=thread.id,
                    object_name=thread.name,
                    object_type="thread",
                    category_id=channel.category_id,
                    category_name=channel.category_name,
                    channel_id=channel.id,
                    channel_name=channel.name,
                    thread_id=thread.id,
                    thread_name=thread.name,
                    system_prompt=channel_prompt
                )
            )

        logger.info(f"Starting AI analysis tasks on {len(analysis_tasks)} objects.")
        await asyncio.gather(*analysis_tasks)

        logger.info("AI analysis completed!")


def get_context_system_prompt(session: Session,
                              server_id: int,
                              category_id: int | None = None,
                              channel_id: int | None = None
                              ) -> str:
    """Get the system prompt for a server from the ContextSystemPrompt table"""

    context_route = f"{server_id}"
    if category_id is not None:
        context_route += f"/{category_id}"
    if channel_id is not None:
        if category_id is None:
            context_route += "/0"
        context_route += f"/{channel_id}"
    prompt_obj = session.exec(
        select(ContextSystemPrompt).where(ContextSystemPrompt.context_route == context_route)
    ).first()

    if prompt_obj and prompt_obj.system_prompt:
        return prompt_obj.system_prompt
    return ""


async def analyze_object(
        session: Session,
        server_id: int,
        server_name: str,
        object_id: int,
        object_name: str,
        object_type: str,
        system_prompt: str,
        category_id: int | None = None,
        category_name: str | None = None,

        channel_id: int | None = None,
        channel_name: str | None = None,

        thread_id: int | None = None,
        thread_name: str | None = None) -> None:
    """
    Run AI analysis on a server object (server, category, or channel)
    and store the results in the ServerObjectAiAnalysis table.
    """
    # Get text content based on object type
    text_to_analyze = get_object_text(session=session,
                                      object_id=object_id,
                                      object_type=object_type)
    if not text_to_analyze:
        logger.warning(f"No text content found for {object_type} - {object_name} (ID: {object_id})")
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


def get_object_text(session: Session, object_id: int, object_type: str) -> str:
    """Get all text content for a given object (server, category, or channel)"""
    if object_type == "server":
        # Get all messages in the server
        threads = session.exec(
            select(Thread).join(Channel).where(Channel.server_id == object_id)
        ).all()
    elif object_type == "category":
        # Get all messages in channels belonging to the category
        threads = session.exec(
            select(Thread).join(Channel).where(Channel.category_id == object_id)
        ).all()
    elif object_type == "channel":
        # Get all messages in the channel
        threads = session.exec(
            select(Thread).where(Thread.channel_id == object_id)
        ).all()
    elif object_type == "thread":
        # Get all messages in the thread
        threads = session.exec(
            select(Thread).where(Thread.id == object_id)
        ).all()
    else:
        logger.error(f"Unknown object type: {object_type}")
        return ""

    # Format messages as text
    thread_texts = []
    for thread in threads:
        messages = session.exec(
            select(Message).where(Message.thread_id == object_id)
        ).all()
        # ensure sorting by timestamp
        messages.sort(key=lambda x: x.timestamp)
        if not messages:
            logger.warning(f"Thread {thread.name} (id: {thread.id}) has no messages, skipping analysis.")
            continue
        if thread.name == ".":
            if len(messages) < MIN_MESSAGE_LIMIT:
                logger.warning(f"Thread {thread.name} has less than {MIN_MESSAGE_LIMIT} messages, skipping analysis.")
                continue
        thread_text = f"Thread: {thread.name} (id: {thread.id})\n\nurl: {messages[0].jump_url}\n\n"
        for msg in messages:
            if msg.is_bot:
                author_name = "- **BOT**"
            else:
                author_name = "- **HUMAN**"
            thread_text += f"{author_name}: {msg.content}\n\n"
            if msg.attachments:
                thread_text += "\n\nBEGIN MESSAGE ATTACHMENTS\n\n"
                for attachment in msg.attachments:
                    thread_text += f"\n\nAttachment: {attachment}"
                thread_text += "\n\nEND MESSAGE ATTACHMENTS\n\n"
        thread_texts.append(thread_text)
    return "\n\n_______________\n\n_______________\n\n".join(thread_texts)


async def analyze_text(text_to_analyze: str, system_prompt: str) -> TextAnalysisPromptModel:
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
        for topic in analysis_result.topic_areas:
            topic.id  = uuid.uuid4()

        # Update message for subsequent chunks
        if chunk_number < len(text_chunks) - 1:
            chunk_based_message = (
                f"Here is chunk #{chunk_number + 2} out of {len(text_chunks)}. "
                f"Here is the running AI analysis of the previous chunk(s):\n"
                f"{analysis_result.model_dump_json(indent=2)}\n\n"
                f"Use the previous results in conjunction with the new text to continue the analysis."
            )

    return analysis_result


def store_analysis_result(
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
        existing.topic_areas = analysis_result.topic_areas
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
            topic_areas=analysis_result.topic_areas
        )
        session.add(analysis)

    session.commit()


if __name__ == "__main__":
    asyncio.run(db_analyze_server_data())
