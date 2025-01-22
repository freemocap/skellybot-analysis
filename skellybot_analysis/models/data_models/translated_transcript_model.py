from httpcore import Origin
from pydantic import BaseModel, Field

from skellybot_analysis.models.data_models.whisper_transcript_result_full_model import \
    WhisperTranscriptionResult

LanguageNameString = str
RomanizationMethodString = str
RomanizedTextString = str
TranslatedTextString = str
OriginalTextString = str

StartingTimestamp = float
EndingTimestamp = float

class LanguagePair(BaseModel):
    language: LanguageNameString = Field(description="The name of the target language")
    romanization_method: RomanizationMethodString | None = Field(default=None, description="The method used to romanize the translated text, if applicable")

class TranslatedText(BaseModel):
    translated_text: TranslatedTextString = Field(description="The translated text in the target language, using the target language's script, characters, and/or alphabet")
    translated_language: LanguageNameString = Field(description="The name of the target language")
    romanization_method: LanguageNameString | None = Field(default=None, description="The method used to romanize the translated text, if applicable")
    romanized_text: RomanizedTextString|None = Field(default=None, description="The romanized version of the translated text, if applicable")

    @classmethod
    def initialize(cls, language: LanguagePair):
        return cls(translated_text="Not yet translated",
                   translated_language=language.language,
                   romanization_method=language.romanization_method,
                   romanized_text="Not yet translated")

TranslationsDict = dict[LanguageNameString, TranslatedText]

class TranslatedWhisperWordTimestamp(BaseModel):
    start: StartingTimestamp = Field(description="The start time of the period in the segment when the word was spoken, in seconds since the start of the recording. Should match the end time of the previous word in the segment or the start time of the segment for the first word.")
    end: EndingTimestamp = Field(description="The end time of the period in the recording when the word was spoken, in seconds since the start of the recording. Should match the start time of the next word in the segment or the end time of the segment for the last word.")
    original_word: OriginalTextString = Field(description="The original word spoken in the segment, in its original language")
    translations: TranslationsDict = Field(description="The translations of the original word into the target languages with their romanizations")

class TranslatedWhisperTranscriptSegment(BaseModel):
    original_text: OriginalTextString = Field(description="The original text of the segment in its original language")
    translations: TranslationsDict = Field(description="The translations of the original text into the target languages with their romanizations")
    start: StartingTimestamp = Field(description="The start time of the period in the recording when the segment was spoken in seconds since the start of the recording. Should match the end time of the previous segment or the start time of the recording for the first segment.")
    end: EndingTimestamp = Field(description="The end time of the segment in the recording when the segment was spoken in seconds since the start of the recording. Should match the start time of the next segment or the end time of the recording for the last segment.")
    words: list[TranslatedWhisperWordTimestamp] = Field(description="Timestamped words in the segment, with translations and romanizations")

class TranslatedTranscription(BaseModel):
    original_text: OriginalTextString = Field(description="The original text of the transcription in its original language")
    translations: TranslationsDict = Field(description="The translations of the original text into the target languages with their romanizations")
    segments: list[TranslatedWhisperTranscriptSegment] = Field(description="Timestamped segments of the original text, with translations and romanizations")

    @property
    def translated_language_pairs(self) -> list[LanguagePair]:
        return [LanguagePair(language=language, romanization_method=translation.romanization_method) for language, translation in self.translations.items()]

    @classmethod
    def initialize(cls, og_transcription: WhisperTranscriptionResult, target_languages: list[LanguagePair]):
        translations = {}
        for language in target_languages:
            translations[language.language] = TranslatedText.initialize(language)

        segments = []
        for segment in og_transcription.segments:
            segments.append(TranslatedWhisperTranscriptSegment(original_text=segment.text,
                                                               translations=translations,
                                                               start=segment.start,
                                                               end=segment.end,
                                                                words=[TranslatedWhisperWordTimestamp(start=word.start,
                                                                                                         end=word.end,
                                                                                                         original_word=word.word,
                                                                                                         translations=translations) for word in segment.words])
                            )
        return cls(original_text=og_transcription.text,
                     translations=translations,
                     segments=segments)

if __name__ == '__main__':
    from pprint import pprint

    outer_og_transcription = WhisperTranscriptionResult(text="This is a test transcription",
                                                  segments=[],
                                                  language="ENGLISH")
    outer_target_languages = [LanguagePair(language="SPANISH", romanization_method=None),
                        LanguagePair(language="ARABIC-LEVANTINE", romanization_method="ALA-LC")]

    translated_transcription = TranslatedTranscription.initialize(outer_og_transcription, outer_target_languages)

    pprint(translated_transcription.model_dump(), indent=2)