from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.make_openai_text_generation_ai_request import \
    make_openai_text_generation_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import OPENAI_CLIENT, DEFAULT_LLM
from skellybot_analysis.models.data_models.simple_transcript_results_model import SimpleWhisperTranscriptionResult
from skellybot_analysis.models.prompt_models.transcript_translation_prompt_model import \
    TranscriptTranslationPromptModel, format_transcript_translation_system_prompt


async def translate_transcription_result(original_transcription_text: str,
                                         original_language: str,
                                         target_language: str,
                                         romanization:str|None=None,
                                         verbose: bool = False
                                         ) -> TranscriptTranslationPromptModel:
    system_prompt = format_transcript_translation_system_prompt(
        original_transcription_result_str= original_transcription_text,
        original_language=original_language,
        romanization=romanization,
        target_language=target_language)
    if verbose:
        print(f"Running `translate_transcription_result` pipeline with system_prompt=\n\n{system_prompt}")
    transcript_translation_ai_result = await make_openai_text_generation_ai_request(client=OPENAI_CLIENT,
                                                         system_prompt=system_prompt,
                                                         llm_model=DEFAULT_LLM
                                                         )
    if verbose:
        print(f"transcript_translation_ai_result=\n{transcript_translation_ai_result.model_dump_json(indent=2)}")
    return transcript_translation_ai_result
