from enum import Enum

from pydantic import BaseModel, Field

from skellybot_analysis.ai.audio_transcription.whisper_transcript_result_full_model import \
    WhisperTranscriptionResult

LanguageNameString = str
RomanizationMethodString = str
RomanizedTextString = str
TranslatedTextString = str
OriginalTextString = str

StartingTimestamp = float
EndingTimestamp = float

NOT_TRANSLATED_YET_TEXT = "NOT-TRANSLATED-YET"


class LanguageNames(str, Enum):
    ENGLISH = "ENGLISH"
    SPANISH = "SPANISH"
    CHINESE_MANDARIN_SIMPLIFIED = "CHINESE_MANDARIN_SIMPLIFIED"
    ARABIC_LEVANTINE = "ARABIC_LEVANTINE"


class RomanizationMethods(str, Enum):
    NONE = 'NONE'
    PINYIN = "PINYIN"
    ALA_LC = "ALA-LC"


class LanguagePairs(tuple[LanguageNames, RomanizationMethods]):
    ENGLISH = (LanguageNames.ENGLISH, RomanizationMethods.NONE)
    SPANISH = (LanguageNames.SPANISH, RomanizationMethods.NONE)
    CHINESE_MANDARIN_SIMPLIFIED = (LanguageNames.CHINESE_MANDARIN_SIMPLIFIED, RomanizationMethods.PINYIN)
    ARABIC_LEVANTINE = (LanguageNames.ARABIC_LEVANTINE, RomanizationMethods.ALA_LC)


class LanguagePair(BaseModel):
    language: LanguageNameString = Field(description="The name of the target language")
    romanization_method: RomanizationMethodString = Field(
        description="The method used to romanize the translated text, if applicable")

    @classmethod
    def from_enum(cls, language_pair: tuple[LanguageNames, RomanizationMethods]):
        return cls(language=language_pair[0], romanization_method=language_pair[1])


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

    @classmethod
    def create(cls):
        return cls(spanish=TranslatedText.initialize(LanguagePair.from_enum(LanguagePairs.SPANISH)),
                   chinese=TranslatedText.initialize(LanguagePair.from_enum(LanguagePairs.CHINESE_MANDARIN_SIMPLIFIED)),
                   arabic=TranslatedText.initialize(LanguagePair.from_enum(LanguagePairs.ARABIC_LEVANTINE)))

    def languages_and_romanizations(self) -> dict[LanguageNameString, RomanizationMethodString]:
        return {LanguageNames.SPANISH.value: self.spanish.romanization_method,
                LanguageNames.CHINESE_MANDARIN_SIMPLIFIED.value: self.chinese.romanization_method,
                LanguageNames.ARABIC_LEVANTINE.value: self.arabic.romanization_method}


class WordType(BaseModel):
    type: str = Field(description="The type of word, e.g. noun, verb, etc.")
    slang: bool | None = Field(default=None,
                               description="Whether the word is slang or not, e.g. informal language, etc.")
    definition: str | None = Field(default=None, description="The definition of the word, if applicable")
    onomatopoeia: bool | None = Field(default=None,
                                      description="Whether the word is an onomatopoeia or not, e.g. a word that sounds like the sound it describes, etc.")


class NounType(WordType):
    type: str = Field(default="noun", description="The type of word, e.g. noun, verb, etc.")
    proper_name: bool | None = Field(default=None,
                                     description="Whether the word is a proper name or not, e.g. a person's name, a place name, etc.")
    animate_object: bool | None = Field(default=None,
                                        description="Whether the word refers to an animate object, e.g. a person, animal, etc.")
    abstract_object: bool | None = Field(default=None,
                                         description="Whether the word refers to an abstract object, e.g. an idea, concept, etc.")
    countable_object: bool | None = Field(default=None,
                                          description="Whether the word refers to a countable object, e.g. a chair, a book, etc.")
    mass_object: bool | None = Field(default=None,
                                     description="Whether the word refers to a mass object, e.g. water, air, etc.")


class VerbType(WordType):
    type: str = Field(default="verb", description="The type of word, e.g. noun, verb, etc.")
    transitive: bool | None = Field(default=None,
                                    description="Whether the verb is transitive or not, e.g. requires a direct object, etc.")
    tense: str | None = Field(default=None, description="The tense of the verb, e.g. past, present, future, etc.")


class AdjectiveType(WordType):
    type: str = Field(default="adjective", description="The type of word, e.g. noun, verb, etc.")
    comparative: bool | None = Field(default=None,
                                     description="Whether the adjective is comparative or not, e.g. taller, shorter, etc.")
    superlative: bool | None = Field(default=None,
                                     description="Whether the adjective is superlative or not, e.g. tallest, shortest, etc.")


class AdverbType(WordType):
    type: str = Field(default="adverb", description="The type of word, e.g. noun, verb, etc.")
    comparative: bool | None = Field(default=None,
                                     description="Whether the adverb is comparative or not, e.g. more quickly, etc.")
    superlative: bool | None = Field(default=None,
                                     description="Whether the adverb is superlative or not, e.g. most quickly, etc.")


class PronounType(WordType):
    type: str = Field(default="pronoun", description="The type of word, e.g. noun, verb, etc.")
    person: int | None = Field(default=None,
                               description="The person of the pronoun, e.g. first person, second person, third person, etc.")
    number: int | None = Field(default=None, description="The number of the pronoun, e.g. singular, plural etc.")
    formality: str | None = Field(default=None,
                                  description="The formality of the pronoun, e.g. formal, informal, etc (if applicable, else None).")


class TranslatedWhisperWordTimestamp(BaseModel):
    start: StartingTimestamp = Field(
        description="The start time of the period in the segment when the word was spoken, in seconds since the start of the recording. Should match the end time of the previous word in the segment or the start time of the segment for the first word.")
    end: EndingTimestamp = Field(
        description="The end time of the period in the recording when the word was spoken, in seconds since the start of the recording. Should match the start time of the next word in the segment or the end time of the segment for the last word.")
    original_word: OriginalTextString = Field(
        description="The original word spoken in the segment, in its original language")
    translations: TranslationsCollection = Field(
        description="The translations of the original word into the target languages with their romanizations")
    word_type: WordType | None = Field(default=None,
                                       description="Linguistic features of the word, such as part of speech, tense, etc.")


class TranslatedTranscriptSegment(BaseModel):
    original_text: OriginalTextString = Field(description="The original text of the segment in its original language")
    translations: TranslationsCollection = Field(
        description="The translations of the original text into the target languages with their romanizations")
    start: StartingTimestamp = Field(
        description="The start time of the period in the recording when the segment was spoken in seconds since the start of the recording. Should match the end time of the previous segment or the start time of the recording for the first segment.")
    end: EndingTimestamp = Field(
        description="The end time of the segment in the recording when the segment was spoken in seconds since the start of the recording. Should match the start time of the next segment or the end time of the recording for the last segment.")


class TranslatedTranscriptSegmentWithWordTimestamps(TranslatedTranscriptSegment):
    words: list[TranslatedWhisperWordTimestamp] = Field(
        description="Timestamped words in the segment, with translations and romanizations")


class TranslatedTranscription(BaseModel):
    original_text: OriginalTextString = Field(
        description="The original text of the transcription in its original language")
    original_language: LanguageNameString = Field(description="The name of the original language of the transcription")
    translations: TranslationsCollection = Field(
        description="The translations of the original text into the target languages with their romanizations")
    segments: list[TranslatedTranscriptSegment] = Field(  # | TranslatedTranscriptSegmentWithWordTimestamps
        description="Timestamped segments of the original text, with translations and romanizations")

    @property
    def translated_language_pairs(self) -> dict[LanguageNameString, RomanizationMethodString]:
        return self.translations.languages_and_romanizations()

    @property
    def target_languages_as_string(self) -> str:
        return ', '.join([f"Language: {language} (Romanization method: {romanization})" for language, romanization in self.translated_language_pairs.items()])

    @classmethod
    def initialize(cls,
                   og_transcription: WhisperTranscriptionResult):
        segments = []
        for segment in og_transcription.segments:
            segments.append(TranslatedTranscriptSegment(original_text=segment.text,
                                                        translations=TranslationsCollection.create(),
                                                        start=segment.start,
                                                        end=segment.end,
                                                        # words=[TranslatedWhisperWordTimestamp(
                                                        #     start=word.start,
                                                        #     end=word.end,
                                                        #     original_word=word.word,
                                                        #     translations=translations) for word in
                                                        #     segment.words]
                                                        )
                            )
        return cls(original_text=og_transcription.text,
                   original_language=LanguageNames.ENGLISH.value,
                   translations=TranslationsCollection.create(),
                   segments=segments)

    def without_words(self) -> 'TranslatedTranscription':
        return TranslatedTranscription(original_text=self.original_text,
                                       translations=self.translations,
                                       segments=[TranslatedTranscriptSegment(original_text=segment.original_text,
                                                                             translations=segment.translations,
                                                                             start=segment.start,
                                                                             end=segment.end)
                                                 for segment in self.segments])


if __name__ == '__main__':
    from pprint import pprint

    outer_og_transcription = WhisperTranscriptionResult(text="This is a test transcription",
                                                        segments=[],
                                                        language=LanguageNames.ENGLISH.value)

    translated_transcription = TranslatedTranscription.initialize(og_transcription=outer_og_transcription,
                                                                  original_language=LanguageNames.ENGLISH.value)

    print(f"INITIALIZED TRANSLATED TRANSCRIPTION")
    pprint(translated_transcription.model_dump(), indent=2)

    print(f"TRANSLATED TRANSCRIPT JSON MODEL SCHEMA")
    pprint(translated_transcription.model_json_schema(), indent=2)
