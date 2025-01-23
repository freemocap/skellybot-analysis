from skellybot_analysis.ai.audio_transcription.whisper_transcript_result_full_model import WhisperTranscriptionResult
from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import OPENAI_CLIENT, DEFAULT_LLM
from skellybot_analysis.ai.pipelines.add_subtitles_to_video_pipeline.full_text_transcript_translation_prompt import \
    format_full_segement_level_transcript_translation_system_prompt
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import \
    TranslatedTranscription, TranslatedTranscriptionWithoutWords

import logging
logger = logging.getLogger(__name__)

async def translate_transcription_pipeline(og_transcription: WhisperTranscriptionResult,
                                           verbose: bool = True
                                           ) -> TranslatedTranscription:
    # Full-text & segment level translation
    segment_level_system_prompt = format_full_segement_level_transcript_translation_system_prompt(
        initialized_translated_transcript_without_words=TranslatedTranscriptionWithoutWords.initialize(og_transcription=og_transcription))

    segment_level_translated_transcript = await make_openai_json_mode_ai_request(client=OPENAI_CLIENT,
                                                                   system_prompt=segment_level_system_prompt,
                                                                   llm_model=DEFAULT_LLM,
                                                                   user_input=None,
                                                                   prompt_model=TranslatedTranscriptionWithoutWords,
                                                                   )
    logger.debug(f"Segment-level translation result: \n\n{segment_level_translated_transcript.model_dump_json(indent=2)}\n\n"
                 f"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n")
    # # Word-level translation
    # word_translation_system_prompt = format_word_level_transcript_translation_system_prompt(
    #     initialized_translated_transcript_object=initialized_translated_transcript_object,
    #     verbose=verbose)
    # if verbose:
    #     print(f"segment_level_system_prompt=\n{segment_level_system_prompt}")
    #     print(
    #         f"initialized_translated_transcript_object=\n{initialized_translated_transcript_object.model_dump_json(indent=2)}")
    #     # print(f"prompt_model=TranslatedTranscription.model_json_schema=\n{json.dumps(TranslatedTranscription.model_json_schema(), indent=2)}")
    # translated_transcript = await make_openai_json_mode_ai_request(client=OPENAI_CLIENT,
    #                                                                system_prompt=segment_level_system_prompt,
    #                                                                llm_model=DEFAULT_LLM,
    #                                                                user_input=None,
    #                                                                prompt_model=TranslatedTranscription,
    #                                                                )
    #
    # if verbose:
    #     print(f"transcript_translation_ai_result=\n{translated_transcript.model_dump_json(indent=2)}")

    return segment_level_translated_transcript
