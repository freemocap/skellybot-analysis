from skellybot_analysis.ai.pipelines.add_subtitles_to_video_pipeline.full_text_transcript_translation_prompt import \
    BASE_TRANSLATION_PROMPT
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import \
    TranslatedTranscription

SEGMENT_WORD_LEVEL_TASK_INSTRUCTIONS = """
You will be given the result of a Whisper transcription of an audio recording in {original_language} which has already been translated into the following languages: 

{target_languages}

Your job is to augment the existing full-text and segment-level translations with word-level translations, romanization and linguisitic annotation and categorization.

Using the provided information, you should complete the following tasks:

    1.  Provide a translation of the word spoken in the original language into the target language and romanization  (Primary task)
    2.  Categorize the linguistic features of the word spoken in the original language (e.g. part of speech, etc)
    3.  OPTIONAL - Provide any additional linguistic or contextual annotations that you think are relevant to the translation of the word spoken in the original language into the target language (in general and within the specific context of the transcript)

 Considerations:
    - It is ok to use the multiple words from the target language to fit the translation of a single word in the original language, 
    - You may use the same word or phrase from the target language multiple times if you need to.
    - You may take words from the target language out of order if it helps to match the best translation of the word spoken in the original language. 
"""

SEGMENT_WORD_LEVEL_TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT = """
{base_translation_prompt}

{segment_word_level_task_instructions}

Here is the full text of the transcript in {original_language} and its translations into the target languages:

{full_translated_text}

You are currently augmenting the translation of Segment#{segment_number} (of {total_segment_count}), here it is in the original language and its translations:

{segment_translated_text}

Here is the initialized list of word-level timestamps for the original language text:

{untranslated_segment_words_list} 

REMEMBER! Your task is:
{segment_word_level_task_instructions_repeated}
"""

def format_segment_word_level_transcript_translation_system_prompts(
        initialized_translated_transcript: TranslatedTranscription) -> dict[int, str]:
    segment_word_level_task_instructions = SEGMENT_WORD_LEVEL_TASK_INSTRUCTIONS.format(
        original_language=initialized_translated_transcript.original_language,
        target_languages=initialized_translated_transcript.target_languages_as_string
    )
    prompt_by_segment: dict[int, str] = {}
    for segment_number, segment in enumerate(initialized_translated_transcript.segments):
        prompt_by_segment[segment_number] = SEGMENT_WORD_LEVEL_TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT.format(
            base_translation_prompt=BASE_TRANSLATION_PROMPT,
            segment_word_level_task_instructions=segment_word_level_task_instructions,
            full_translated_text=initialized_translated_transcript.translated_text.as_string,
            segment_number=segment_number,
            total_segment_count=len(initialized_translated_transcript.segments),
            segment_translated_text=segment.translated_text.as_string,
            words_list=segment.words_list_as_string,
        )

    return prompt_by_segment
