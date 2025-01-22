
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
        return cls(translated_text="NOT YET TRANSLATED",
                   translated_language=language.language,
                   romanization_method=language.romanization_method,
                   romanized_text="NOT YET TRANSLATED")

TranslationsDict = dict[LanguageNameString, TranslatedText]



class WordType(BaseModel):
    type : str = Field(description="The type of word, e.g. noun, verb, etc.")
    slang: bool | None = Field(default=None, description="Whether the word is slang or not, e.g. informal language, etc.")
    definition: str | None = Field(default=None, description="The definition of the word, if applicable")
    onomatopoeia: bool | None = Field(default=None, description="Whether the word is an onomatopoeia or not, e.g. a word that sounds like the sound it describes, etc.")

class NounType(WordType):
    type: str = Field(default="noun", description="The type of word, e.g. noun, verb, etc.")
    proper_name: bool | None = Field(default=None, description="Whether the word is a proper name or not, e.g. a person's name, a place name, etc.")
    animate_object: bool | None = Field(default=None, description="Whether the word refers to an animate object, e.g. a person, animal, etc.")
    abstract_object: bool | None = Field(default=None, description="Whether the word refers to an abstract object, e.g. an idea, concept, etc.")
    countable_object: bool | None = Field(default=None, description="Whether the word refers to a countable object, e.g. a chair, a book, etc.")
    mass_object: bool | None = Field(default=None, description="Whether the word refers to a mass object, e.g. water, air, etc.")

class VerbType(WordType):
    type: str = Field(default="verb", description="The type of word, e.g. noun, verb, etc.")
    transitive: bool | None = Field(default=None, description="Whether the verb is transitive or not, e.g. requires a direct object, etc.")
    tense: str | None = Field(default=None, description="The tense of the verb, e.g. past, present, future, etc.")

class AdjectiveType(WordType):
    type: str = Field(default="adjective", description="The type of word, e.g. noun, verb, etc.")
    comparative: bool | None = Field(default=None, description="Whether the adjective is comparative or not, e.g. taller, shorter, etc.")
    superlative: bool | None = Field(default=None, description="Whether the adjective is superlative or not, e.g. tallest, shortest, etc.")

class AdverbType(WordType):
    type: str = Field(default="adverb", description="The type of word, e.g. noun, verb, etc.")
    comparative: bool | None = Field(default=None, description="Whether the adverb is comparative or not, e.g. more quickly, etc.")
    superlative: bool | None = Field(default=None, description="Whether the adverb is superlative or not, e.g. most quickly, etc.")

class PronounType(WordType):
    type: str = Field(default="pronoun", description="The type of word, e.g. noun, verb, etc.")
    person: int | None = Field(default=None, description="The person of the pronoun, e.g. first person, second person, third person, etc.")
    number: int | None = Field(default=None, description="The number of the pronoun, e.g. singular, plural etc.")
    formality: str | None = Field(default=None, description="The formality of the pronoun, e.g. formal, informal, etc (if applicable, else None).")

class TranslatedWhisperWordTimestamp(BaseModel):
    start: StartingTimestamp = Field(description="The start time of the period in the segment when the word was spoken, in seconds since the start of the recording. Should match the end time of the previous word in the segment or the start time of the segment for the first word.")
    end: EndingTimestamp = Field(description="The end time of the period in the recording when the word was spoken, in seconds since the start of the recording. Should match the start time of the next word in the segment or the end time of the segment for the last word.")
    original_word: OriginalTextString = Field(description="The original word spoken in the segment, in its original language")
    translations: TranslationsDict = Field(description="The translations of the original word into the target languages with their romanizations")
    word_type: WordType = Field(description="Linguistic features of the word, such as part of speech, tense, etc.")


class TranslatedTranscriptSegment(BaseModel):
    original_text: OriginalTextString = Field(description="The original text of the segment in its original language")
    translations: TranslationsDict = Field(description="The translations of the original text into the target languages with their romanizations")
    start: StartingTimestamp = Field(description="The start time of the period in the recording when the segment was spoken in seconds since the start of the recording. Should match the end time of the previous segment or the start time of the recording for the first segment.")
    end: EndingTimestamp = Field(description="The end time of the segment in the recording when the segment was spoken in seconds since the start of the recording. Should match the start time of the next segment or the end time of the recording for the last segment.")


class TranslatedTranscriptSegmentWithWordTimestamps(TranslatedTranscriptSegment):
    words: list[TranslatedWhisperWordTimestamp] = Field(description="Timestamped words in the segment, with translations and romanizations")


class TranslatedTranscription(BaseModel):
    original_text: OriginalTextString = Field(description="The original text of the transcription in its original language")
    translations: TranslationsDict = Field(description="The translations of the original text into the target languages with their romanizations")
    segments: list[TranslatedTranscriptSegment | TranslatedTranscriptSegmentWithWordTimestamps ] = Field(description="Timestamped segments of the original text, with translations and romanizations")

    @property
    def translated_language_pairs(self) -> list[LanguagePair]:
        return [LanguagePair(language=language, romanization_method=translation.romanization_method) for language, translation in self.translations.items()]

    @property
    def target_languages_as_string(self) -> str:
        return ", ".join([f"{language} (Romanization: {translation.romanization_method})" if translation.romanization_method else language for language, translation in self.translations.items()])

    @classmethod
    def initialize(cls, og_transcription: WhisperTranscriptionResult, target_languages: list[LanguagePair]):
        translations = {}
        for language in target_languages:
            translations[language.language] = TranslatedText.initialize(language)

        segments = []
        for segment in og_transcription.segments:
            segments.append(TranslatedTranscriptSegmentWithWordTimestamps(original_text=segment.text,
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
                                                  language="ENGLISH")
    outer_target_languages = [LanguagePair(language="SPANISH", romanization_method=None),
                        LanguagePair(language="ARABIC-LEVANTINE", romanization_method="ALA-LC")]

    translated_transcription = TranslatedTranscription.initialize(outer_og_transcription, outer_target_languages)

    pprint(translated_transcription.model_dump(), indent=2)