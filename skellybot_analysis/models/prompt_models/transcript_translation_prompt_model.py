from typing import List
from pydantic import BaseModel, Field


TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT = """
You will be given the result of a Whisper transcription of an audio recording in {original_language}.

You will be asked to provide a translation of the text into {target_language}, and to provide timestamps for corresponding segments and words from the original transcription result.

Use the timestamps provided to segment the text into translated segments, which should then be broken down into individual words with their corresponding timestamps.
The end_timestamp of a segment or word should match the start_timestamp of the next segment or word.

Here is the Whisper output from the original audio recording:

{original_text}

Provide the translation of the text into {target_language}, and the corresponding timestamps for the translated segments and words.

"""

def format_transcript_translation_system_prompt(original_transcription_result_json_str:str,
                                                original_language:str,
                                                target_language:str) -> str:
    if any([original_language is None, target_language is None, original_transcription_result_json_str is None]):
        raise ValueError("Error: Missing required parameters: original_language={original_language}, target_language={target_language}, original_text={original_text}")
    if any([len(original_language) == 0, len(target_language) == 0, len(original_transcription_result_json_str) == 0]):
        raise ValueError(f"Error: Empty required parameters: original_language={original_language}, target_language={target_language}, original_text={original_transcription_result_json_str}")
    return TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT.format(original_language=original_language, target_language=target_language, original_text=original_transcription_result_json_str)

class TranslatedWordTimestampModel(BaseModel):
    word: str = Field(description="The translated word.")
    start_timestamp: str = Field(description="The start timestamp of the word.")
    end_timestamp: str = Field(description="The end timestamp of the word, which should match the start timestamp of the next word.")

class TranslatedTextSegmentModel(BaseModel):
    start_timestamp: str = Field(description="The start timestamp of the segment.")
    end_timestamp: str = Field(description="The end timestamp of the segment, which should match the start timestamp of the next segment.")
    translated_text: str = Field(description="The translated text of the segment.")
    words: List[TranslatedWordTimestampModel] = Field(description="The translated words of the segment, with their corresponding timestamps.")

class TranscriptTranslationPromptModel(BaseModel):
    translated_text: str = Field(description="The translated text of the conversation.")
    translated_timestamped_segments: List[TranslatedTextSegmentModel] = Field(description="The translated timestamp segments of the conversation. The first and last timestamps MUST match the original text's timestamps")