from pydantic import BaseModel

from skellybot_analysis.models.data_models.whisper_transcript_result_full_model import \
    WhisperTranscriptionResult


class SimpleWhisperWordTimestamp(BaseModel):
    start: float
    end: float
    word: str

class SimpleWhisperTranscriptSegment(BaseModel):
    text: str
    start: float
    end: float


class SimpleWhisperTranscriptionResult(BaseModel):
    text: str
    segments: list[SimpleWhisperTranscriptSegment]

    @classmethod
    def from_whisper_transcription_result(cls, whisper_transcription_result: WhisperTranscriptionResult):
        segments = []
        for segment in whisper_transcription_result.segments:
            words = []
            for word in segment.words:
                words.append(SimpleWhisperWordTimestamp(start=word.start,
                                                        end=word.end,
                                                        word=word.word))
            segments.append(SimpleWhisperTranscriptSegment(text=segment.text,
                                                            start=segment.start,
                                                            end=segment.end))
        return cls(text=whisper_transcription_result.text,
                   segments=segments)
