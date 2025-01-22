from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import TranslatedTranscription

SEGMENT_LEVEL_TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT = """
You are an expert translator, fluent in the following languages: {languages}. You are trained in audio transcription and translation, and have been trained in the proper way to romanize languages that do not use the Latin alphabet (such as Chinese or Arabic).

You will be given the result of a Whisper transcription of an audio recording in {original_language}, and asked to provide a translation of the full text and a list of the timestamped segments that make up the full transcript. Your job is to translate the original text into each of the target lanauages defined in the initialized TranslatedTranscription object.

You should begin by translating the entire text, and then break it up into segments to match the original transcription (Keep the original timestamps!)

Make sure that all requested languages are translated accurately and that any romanizations are correct. Make sure that all languages cover the full meaning of the original transcribed text. 

Remember, this is an audio transcription, so the text may contain errors. Please do your best to provide an accurate translation of the transcription and attempt to match the speaker's meaning and intention as closely as possible.

Here is the initialized TranslatedTranscription object that you will be working with, which contains the original text and the target languages you are expected to translate the text into (including any romanization requirements) - Fill in the sections that say "NOT YET TRANSLATED" with your translations/romanizations:

{initialized_translated_transcription_object}
"""


def format_segment_level_transcript_translation_system_prompt(
        initialized_translated_transcript_object: TranslatedTranscription,
        verbose: bool = True) -> str:
    prompt = SEGMENT_LEVEL_TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT.format(
        languages=initialized_translated_transcript_object.target_languages_as_string,
        original_language=initialized_translated_transcript_object.original_language,
        initialized_translated_transcription_object=initialized_translated_transcript_object.model_dump_json(indent=2))

    if verbose:
        print(f"Formatted system prompt:\n\n{prompt}")

    return prompt
