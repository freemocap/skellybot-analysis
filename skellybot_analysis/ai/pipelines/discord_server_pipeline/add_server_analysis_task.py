import logging
from typing import Type

from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import MAX_TOKEN_LENGTH, DEFAULT_LLM, OPENAI_CLIENT
from skellybot_analysis.utilities.chunk_text_to_max_token_length import chunk_string_by_max_tokens
from skellybot_analysis.models.data_models.data_object_model import DataObjectModel
from pydantic import BaseModel
logger = logging.getLogger(__name__)


async def add_ai_analysis(thing: DataObjectModel,
                          text_to_analyze: str,
                          system_prompt: str,
                          prompt_model: Type[BaseModel]
                          ):
    print(f"Adding AI analysis to {thing.__class__.__name__}: {thing.name}")
    text_chunks_to_analyze = chunk_string_by_max_tokens(text_to_analyze,
                                                        max_tokens=int(MAX_TOKEN_LENGTH * .8),
                                                        llm_model=DEFAULT_LLM)

    chunk_based_message = ""
    if len(text_chunks_to_analyze)>1:
        print(f"Text to analyze is too long to analyze in one go. Chunking it into {len(text_chunks_to_analyze)} chunks.")
        system_prompt  += (f"The text you are analyzing is too long to analyze in one go."
                           f" You will need to analyze it in chunks.")
        chunk_based_message = f"Here is the chunk#1 out of {len(text_chunks_to_analyze)}:"
    try:
        for chunk_number, text_chunk in enumerate(text_chunks_to_analyze):
            system_prompt += chunk_based_message
            thing.ai_analysis = await make_openai_json_mode_ai_request(client=OPENAI_CLIENT,
                                                                       system_prompt=system_prompt,
                                                                       user_input=text_chunk,
                                                                       prompt_model=prompt_model,
                                                                       llm_model=DEFAULT_LLM)
            chunk_based_message = (f"Here is the chunk {chunk_number+2} out of {len(text_chunks_to_analyze)}:"
                                   f"Here is the running AI analysis of the previous chunk(s):"
                                   f"{thing.ai_analysis.to_string()}"
                                   f"\n\nUse the previous results in conjunction with the new text to continue the analysis of this large body of text.")
    except Exception as e:

        logger.error(f"Error adding AI analysis to {thing.__class__.__name__}: {thing.name}")
        logger.exception(e)
        logger.error(e)
        raise

    print(f"Completed AI analysis to {thing.__class__.__name__}: {thing.name}!")
