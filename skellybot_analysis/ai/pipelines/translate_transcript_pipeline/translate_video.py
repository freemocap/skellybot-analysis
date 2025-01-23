from pathlib import Path

from skellybot_analysis.ai.audio_transcription.translate_whisper_transcription import translate_transcription_pipeline
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.transcribe_video import \
    get_or_compute_video_transcription
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import \
    TranslatedTranscription


async def translate_video(video_path: str, re_transcribe: bool = False) -> TranslatedTranscription:
    if not Path(video_path).exists():
        raise FileNotFoundError(f"File not found: {video_path}")
    if not Path(video_path).is_file():
        raise ValueError(f"Path is not a file: {video_path}")

    transcription_result = await get_or_compute_video_transcription(video_path=video_path, re_transcribe=re_transcribe)

    return await translate_transcription_pipeline(og_transcription=transcription_result)


