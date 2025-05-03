import asyncio
import logging
from asyncio import Task

from openai import LengthFinishReasonError
import tiktoken

from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import MAX_TOKEN_LENGTH, DEFAULT_LLM, OPENAI_CLIENT
from skellybot_analysis.data_models.analysis_models import AiThreadAnalysisModel
from skellybot_analysis.df_db.dataframe_handler import DataframeHandler
from skellybot_analysis.data_models.prompt_models import TextAnalysisPromptModel
from skellybot_analysis.data_models.server_models import ThreadModel, ThreadId, MessageModel

MIN_MESSAGE_LIMIT = 4

logger = logging.getLogger(__name__)


async def ai_analyze_threads(dataframe_handler:DataframeHandler) -> dict[ThreadId, AiThreadAnalysisModel]:
    """Run AI analysis on server data stored in a Parquet database"""
    threads:list[ThreadModel] = list(dataframe_handler.threads.values())
    messages:list[MessageModel] = list(dataframe_handler.messages.values())
    analysis_tasks: list[Task[tuple[ThreadId, AiThreadAnalysisModel]]] = []
    # Run analysis on threads
    logger.info(f"Analyzing {len(threads)} threads")
    for thread in threads:
        thread_messages = [message for message in messages if message.thread_id == thread.thread_id]
        # sort messages by timestamp (oldest first)
        thread_messages.sort(key=lambda x: x.timestamp)
        analysis_tasks.append(asyncio.create_task(analyze_thread(thread=thread,
                                                                 thread_messages=thread_messages)))

    logger.info(f"Starting AI analysis tasks on {len(analysis_tasks)} objects.")
    results: list[tuple[ThreadId, AiThreadAnalysisModel]] = await asyncio.gather(*analysis_tasks)
    logger.info(f"AI analysis tasks completed for {len(results)} objects.")

    logger.info("AI analysis completed!")
    return {id: result for id, result in results}


async def analyze_thread(thread: ThreadModel,
                         thread_messages: list[MessageModel]) -> tuple[ThreadId, AiThreadAnalysisModel]:
    # Get text content based on object type
    thread_text_to_analyze = thread.full_text(messages=thread_messages)

    # Initialize tokenizer
    encoder = tiktoken.encoding_for_model(DEFAULT_LLM)
    tokens = encoder.encode(thread_text_to_analyze)

    # Account for schema tokens and truncation message
    MAX_ALLOWED = MAX_TOKEN_LENGTH - 900  # Reserve space for response schema
    TRUNC_MESSAGE = "\n[Omitted for space constraints]\n"
    truncated_tokens = len(encoder.encode(TRUNC_MESSAGE))

    if len(tokens) > (MAX_ALLOWED - truncated_tokens):
        # Calculate available space for content
        keep_tokens = MAX_ALLOWED - truncated_tokens
        head = tokens[:keep_tokens // 2]
        tail = tokens[-keep_tokens // 2:]

        # Rebuild text with truncation message
        thread_text_to_analyze = (
                encoder.decode(head) +
                TRUNC_MESSAGE +
                encoder.decode(tail)
        )

        logger.warning(f"Truncated thread from {len(tokens)} to ~{len(head) + len(tail)} tokens")

    # Enhance system prompt for analysis
    analysis_prompt = (
        f"You are currently reviewing the chat data from the {thread.server_name} Discord server extracting the content "
        f"of the conversations to provide a landscape of the topics that are being discussed. \n\n"
        f"You are currently analyzing the text of a chat thread which occurred at this location in the server:\n\n"
        f"{thread.context_route.as_formatted_text}\n\n"
        f"Here is the text to analyze:\n\n"
        f"BEGIN TEXT TO ANALYZE\n\n"
        f"{thread_text_to_analyze}\n\n"
        f"END TEXT TO ANALYZE\n"
        f"Keep your answers concise and to the point, without sacrificing clarity and coverage. \n\n"
        f"Carefully consider the content of this conversation in order to provide the output prescribed by the provided JSON schema."
    )

        #Run AI analysis

    max_retries = 3
    attempt = 0
    length_warning = "\n\nWARNING: The last response exceeded length limits. Please keep your answer SHORTER while still providing complete information."

    try:
        while attempt < max_retries:
            result: TextAnalysisPromptModel = await make_openai_json_mode_ai_request(
                client=OPENAI_CLIENT,
                system_prompt=analysis_prompt,
                prompt_model=TextAnalysisPromptModel,
                llm_model=DEFAULT_LLM
            )

            logger.info(f"AI analysis completed for Thread {thread.thread_id} ({thread.jump_url}) \n\n- tile: {result.title_slug}, summary: {result.extremely_short_summary}")

            return thread.thread_id, AiThreadAnalysisModel(
                server_id=thread.server_id,
                server_name=thread.server_name,
                category_id=thread.category_id,
                category_name=thread.category_name,
                channel_id=thread.channel_id,
                channel_name=thread.channel_name,
                thread_id=thread.thread_id,
                thread_name=thread.thread_name,
                jump_url=thread.jump_url,
                thread_owner_id=thread.owner_id,
                analysis_prompt=analysis_prompt,
                base_text=thread_text_to_analyze,
                topic_areas= result.topic_areas_as_string,
                **result.model_dump(exclude={'topic_areas'})
            )
        logger.error(f"Max retries exceeded for thread analysis: {thread.thread_id} ({thread.jump_url})")
        raise ValueError("Max retries exceeded for thread analysis")
    except LengthFinishReasonError:
        attempt += 1
        if attempt >= max_retries:
            raise
        logger.warning(
            f"Length error detected on attempt {attempt} - {thread.thread_id} ({thread.jump_url}) - appending STFU to prompt and retrying")
        # Append length warning to original prompt
        analysis_prompt += f" {length_warning} (re-attempt# {attempt} of {max_retries})"
        return None

    except Exception as e:
        logger.error(f"Error analyzing Thread {thread.thread_id}: {e} \n\n\n({thread.jump_url})")
        raise