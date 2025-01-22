from typing import List

from pydantic import BaseModel, Field

SIMPLE_TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT = """
You will be given the result of a Whisper transcription of an audio recording in {original_language}.

You will be asked to provide a translation of the text into {target_language}

Here is the original text you need to translate into {target_language}:

{original_text}

Provide the translation of the text into {target_language}. Remember, this is an audio transcription, so the text may contain errors. Please do your best to provide an accurate translation of the text, as if it had been spoken by a native speaker of the target language.

"""

TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT = """
You will be given the result of a Whisper transcription of an audio recording in {original_language}.

You will be asked to provide a translation of the text into a variety of different languages, some of which may require romanization (if they do not use the Latin alphabet, such as Chinese or Arabic).

You will br provided with the original transcript which was derived from an audio or video recorded in {original_language}, including the full text transcription and a list of timestamped segments (which comprise 
Return your response in a JSON format that matches the provided schema.
"""


def format_transcript_translation_system_prompt(original_language: str,
                                                target_language: str,
                                                verbose:bool=True) -> str:



    prompt = TRANSCRIPT_TRANSLATION_SYSTEM_PROMPT.format(original_language=original_language,
                                                       target_language=target_language)

    if verbose:
        print(f"Formatted system prompt:\n\n{prompt}")

    return prompt
