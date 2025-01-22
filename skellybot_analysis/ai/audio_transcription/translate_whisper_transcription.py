from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import OPENAI_CLIENT, DEFAULT_LLM
from skellybot_analysis.ai.pipelines.add_subtitles_to_video_pipeline.add_subtitles_to_video_pipeline import \
    original_language
from skellybot_analysis.models.data_models.translated_transcript_model import TranslatedTranscription
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.transcript_translation_prompt import \
    format_transcript_translation_system_prompt


async def translate_transcription_result(initialized_translated_transcript_object: TranslatedTranscription,
                                         verbose: bool = False
                                         ) -> TranslatedTranscription:
    original_language = initialized_translated_transcript_object.original_language

    system_prompt = format_transcript_translation_system_prompt(original_language=original_language,
                                                                verbose=verbose)

    translated_transcripts[language_pair.language] = transcript_translation_ai_result = await make_openai_json_mode_ai_request(client=OPENAI_CLIENT,
                                                                              system_prompt=system_prompt,
                                                                              llm_model=DEFAULT_LLM,
                                                                              user_input=None,
                                                                              prompt_model=TranslatedTranscription,
                                                                              )


        if verbose:
            print(f"transcript_translation_ai_result=\n{transcript_translation_ai_result.model_dump_json(indent=2)}")
    return transcript_translation_ai_result
