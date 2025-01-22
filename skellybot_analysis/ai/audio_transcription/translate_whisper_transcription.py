import json
from pathlib import Path

from skellybot_analysis.ai.clients.openai_client.make_openai_json_mode_ai_request import \
    make_openai_json_mode_ai_request
from skellybot_analysis.ai.clients.openai_client.openai_client import OPENAI_CLIENT, DEFAULT_LLM
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.transcript_translation_prompt import \
    format_segment_level_transcript_translation_system_prompt
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import \
    TranslatedTranscription


async def translate_transcription_result(initialized_translated_transcript_object: TranslatedTranscription,
                                         verbose: bool = True
                                         ) -> TranslatedTranscription:
    # Run AI analysis for the full-text and segment level
    segment_level_system_prompt = format_segment_level_transcript_translation_system_prompt(initialized_translated_transcript_object=initialized_translated_transcript_object,
                                                                                            verbose=verbose)
    if verbose:
        schema = TranslatedTranscription.model_json_schema()
        print(f"segment_level_system_prompt=\n{segment_level_system_prompt}")
        print(f"initialized_translated_transcript_object=\n{initialized_translated_transcript_object.model_dump_json(indent=2)}")
        print(f"prompt_model=TranslatedTranscription.model_json_schema=\n{json.dumps(schema, indent=2)}")
    translated_transcript = await make_openai_json_mode_ai_request(client=OPENAI_CLIENT,
                                                                              system_prompt=segment_level_system_prompt,
                                                                              llm_model=DEFAULT_LLM,
                                                                              user_input=None,
                                                                              prompt_model=TranslatedTranscription,
                                                                              )


    if verbose:
        print(f"transcript_translation_ai_result=\n{translated_transcript.model_dump_json(indent=2)}")
    Path("transcript_translation_ai_result.json").write_text(translated_transcript.model_dump_json(indent=2), encoding="utf-8")
    return translated_transcript
