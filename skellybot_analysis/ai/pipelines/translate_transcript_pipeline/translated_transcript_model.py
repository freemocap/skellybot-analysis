import json

from pydantic import BaseModel, Field

from skellybot_analysis.ai.audio_transcription.whisper_transcript_result_full_model import \
    WhisperTranscriptionResult, WhisperWordTimestamp
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.language_models import LanguageNames, LanguagePairs, \
    LanguagePair
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translation_typehints import NOT_TRANSLATED_YET_TEXT, \
    LanguageNameString, RomanizationMethodString, RomanizedTextString, TranslatedTextString, OriginalTextString, \
    StartingTimestamp, EndingTimestamp
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.word_models import WordTypeSchemas


class TranslatedText(BaseModel):
    translated_text: TranslatedTextString = Field(
        description="The translated text in the target language, using the target language's script, characters, and/or alphabet")
    translated_language: LanguageNameString = Field(description="The name of the target language")
    romanization_method: RomanizationMethodString = Field(
        description="The method used to romanize the translated text, if applicable")
    romanized_text: RomanizedTextString = Field(
        description="The romanized version of the translated text, if applicable")

    @classmethod
    def initialize(cls, language: LanguagePair):
        return cls(translated_text=NOT_TRANSLATED_YET_TEXT,
                   translated_language=language.language,
                   romanization_method=language.romanization_method,
                   romanized_text=NOT_TRANSLATED_YET_TEXT)


class TranslationsCollection(BaseModel):
    spanish: TranslatedText = Field(description="The translation of the original text into Spanish")
    chinese: TranslatedText = Field(description="The translation of the original text into Chinese Mandarin Simplified")
    arabic: TranslatedText = Field(description="The translation of the original text into Arabic Levantine")

    @property
    def has_translations(self) -> bool:
        return not any([translation['translated_text'] == NOT_TRANSLATED_YET_TEXT
                        for translation in self.model_dump().values()])

    @classmethod
    def create(cls):
        return cls(spanish=TranslatedText.initialize(LanguagePair.from_enum(LanguagePairs.SPANISH)),
                   chinese=TranslatedText.initialize(LanguagePair.from_enum(LanguagePairs.CHINESE_MANDARIN_SIMPLIFIED)),
                   arabic=TranslatedText.initialize(LanguagePair.from_enum(LanguagePairs.ARABIC_LEVANTINE)))

    def languages_and_romanizations(self) -> dict[LanguageNameString, RomanizationMethodString]:
        return {LanguageNames.SPANISH.value: self.spanish.romanization_method,
                LanguageNames.CHINESE_MANDARIN_SIMPLIFIED.value: self.chinese.romanization_method,
                LanguageNames.ARABIC_LEVANTINE.value: self.arabic.romanization_method}


class TranslatedWhisperWordTimestamp(BaseModel):
    start: StartingTimestamp = Field(
        description="The start time of the period in the segment when the word was spoken, in seconds since the start of the recording. Should match the end time of the previous word in the segment or the start time of the segment for the first word.")
    end: EndingTimestamp = Field(
        description="The end time of the period in the recording when the word was spoken, in seconds since the start of the recording. Should match the start time of the next word in the segment or the end time of the segment for the last word.")
    original_word: OriginalTextString = Field(
        description="The original word spoken in the segment, in its original language")
    translations: TranslationsCollection = Field(
        description="The translations of the original word into the target languages with their romanizations")
    # word_type: WordTypeSchemas|str = Field(default=WordTypeSchemas.OTHER.name,
    #                                    description="Linguistic features of the word, such as part of speech, tense, etc.")

    @classmethod
    def from_whisper_result(cls, word: WhisperWordTimestamp):
        return cls(start=word.start,
                   end=word.end,
                   original_word=word.word,
                   translations=TranslationsCollection.create(),
                   word_type=WordTypeSchemas.NOT_PROCESSED.name)


class TranslatedTranscriptSegmentWithoutWords(BaseModel):
    original_segment_text: OriginalTextString = Field(
        description="The original text of the segment in its original language")
    translations: TranslationsCollection = Field(
        description="The translations of the original text into the target languages with their romanizations")
    start: StartingTimestamp = Field(
        description="The start time of the period in the recording when the segment was spoken in seconds since the start of the recording. Should match the end time of the previous segment or the start time of the recording for the first segment.")
    end: EndingTimestamp = Field(
        description="The end time of the segment in the recording when the segment was spoken in seconds since the start of the recording. Should match the start time of the next segment or the end time of the recording for the last segment.")

    @property
    def og_text_and_translations(self) -> dict:
        return {"original_text": self.original_segment_text,
                **self.translations.model_dump()}

class TranslatedTranscriptSegmentWithWords(TranslatedTranscriptSegmentWithoutWords):
    words: list[TranslatedWhisperWordTimestamp] = Field(
        description="Timestamped words in the segment, with translations and romanizations")

    @property
    def original_words(self) -> str:
        return ', \n'.join([word.model_dump_json(indent=2) for word in self.words])

class TranslatedTranscriptionWithoutWords(BaseModel):
    original_text: OriginalTextString = Field(
        description="The original text of the transcription in its original language")
    original_language: LanguageNameString = Field(description="The name of the original language of the transcription")
    translations: TranslationsCollection = Field(
        description="The translations of the original text into the target languages with their romanizations")
    segments: list[TranslatedTranscriptSegmentWithoutWords] = Field(
        description="Timestamped segments of the original text, with translations and romanizations (excluding word-level timestamps)")

    @property
    def translated_language_pairs(self) -> dict[LanguageNameString, RomanizationMethodString]:
        return self.translations.languages_and_romanizations()

    @property
    def target_languages_as_string(self) -> str:
        return ', '.join([f"Language: {language} (Romanization method: {romanization})" for language, romanization in
                          self.translated_language_pairs.items()])

    @property
    def has_translations(self) -> bool:
        return self.translations.has_translations

    @property
    def og_text_and_translations(self) -> dict:
        return {self.original_language: self.original_text,
                **self.translations.model_dump()}
    @classmethod
    def initialize(cls,
                   og_transcription: WhisperTranscriptionResult):
        segments = []
        for segment in og_transcription.segments:
            segments.append(TranslatedTranscriptSegmentWithoutWords(original_segment_text=segment.text,
                                                                    translations=TranslationsCollection.create(),
                                                                    start=segment.start,
                                                                    end=segment.end,
                                                                    # words=[TranslatedWhisperWordTimestamp.from_whisper_result(word) for word in
                                                                    #     segment.words]
                                                                    )
                            )
        return cls(original_text=og_transcription.text,
                   original_language=LanguageNames.ENGLISH.value,
                   translations=TranslationsCollection.create(),
                   segments=segments)


class TranslatedTranscription(TranslatedTranscriptionWithoutWords):
    segments: list[TranslatedTranscriptSegmentWithWords] = Field(
        description="Timestamped segments of the original text with translations and romanizations (including word-level timestamps)")

    @classmethod
    def from_segment_level_translation(cls,
                                       og_transcription: WhisperTranscriptionResult,
                                       segment_level_translated_transcript: TranslatedTranscriptionWithoutWords):
        if not segment_level_translated_transcript.has_translations:
            raise ValueError(
                "Segment-level translated transcript must have translations to initialize a full translated transcript.")
        segments = []
        for og_segment, translated_segment in zip(og_transcription.segments,
                                                  segment_level_translated_transcript.segments):
            segments.append(TranslatedTranscriptSegmentWithWords(original_segment_text=og_segment.text,
                                                                 translations=translated_segment.translations,
                                                                 start=og_segment.start,
                                                                 end=og_segment.end,
                                                                 words=[
                                                                     TranslatedWhisperWordTimestamp.from_whisper_result(
                                                                         word) for word in
                                                                     og_segment.words]
                                                                 )
                            )
        return cls(original_text=og_transcription.text,
                   original_language=og_transcription.language,
                   translations=segment_level_translated_transcript.translations,
                   segments=segments)


if __name__ == '__main__':
    from pprint import pprint

    outer_og_transcription = WhisperTranscriptionResult(text="This is a test transcription, wowee zoowee",
                                                        segments=[],
                                                        language=LanguageNames.ENGLISH.value)

    translated_transcription = TranslatedTranscription.initialize(og_transcription=outer_og_transcription)

    print(f"INITIALIZED TRANSLATED TRANSCRIPTION")
    pprint(translated_transcription.model_dump(), indent=2)

    print(f"TRANSLATED TRANSCRIPT JSON MODEL SCHEMA")
    pprint(translated_transcription.model_json_schema(), indent=2)
