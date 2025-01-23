import json
from pathlib import Path

from moviepy import VideoFileClip

from skellybot_analysis.ai.audio_transcription.translate_whisper_transcription import translate_transcription_pipeline
from skellybot_analysis.ai.audio_transcription.whisper_transcript_result_full_model import WhisperTranscriptionResult
from skellybot_analysis.ai.audio_transcription.whisper_transcription import transcribe_audio
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import \
    TranslatedTranscription


async def translate_video(video_path: str, re_transcribe: bool = False) -> TranslatedTranscription:
    if not Path(video_path).exists():
        raise FileNotFoundError(f"File not found: {video_path}")
    if not Path(video_path).is_file():
        raise ValueError(f"Path is not a file: {video_path}")

    transcription_result = await get_or_compute_video_transcription(video_path=video_path, re_transcribe=re_transcribe)

    return await translate_transcription_pipeline(og_transcription=transcription_result)


async def get_or_compute_video_transcription(video_path: str,
                                             re_transcribe: bool = False) -> WhisperTranscriptionResult:
    audio_path = video_path.replace(".mp4", ".wav")
    transcript_path = video_path.replace(".mp4", "_transcription.json")
    if Path(transcript_path).exists() and not re_transcribe:
        with open(transcript_path, 'r') as f:
            transcription_json = json.load(f)
        transcription_result = WhisperTranscriptionResult(**transcription_json)
    else:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        transcription_result = transcribe_audio(audio_path)
        Path(transcript_path).write_text(json.dumps(transcription_result.model_dump(), indent=4))
    return transcription_result
