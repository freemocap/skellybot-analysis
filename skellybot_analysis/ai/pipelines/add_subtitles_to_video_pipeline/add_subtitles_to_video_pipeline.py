import json
from pathlib import Path

from skellybot_analysis.ai.pipelines.add_subtitles_to_video_pipeline.video_annotator.annotate_video_with_subtitles_cv2_PIL import \
    annotate_video_with_highlighted_words_cv2_PIL
from skellybot_analysis.ai.pipelines.add_subtitles_to_video_pipeline.video_annotator.annotate_video_with_subtitles_moviepy import \
    annotate_video_with_highlighted_words_moviepy
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translate_video import translate_video
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import \
    TranslatedTranscription


async def run_video_subtitle_pipeline(video_name: str) -> None:

    subtitled_video_path, video_path, translation_path = await get_video_and_output_paths(video_name=video_name)

    if Path(translation_path).exists():
        with open(translation_path, 'r', encoding='utf-8') as f:
            transcription_json = json.load(f)
        translation_result = TranslatedTranscription(**transcription_json)
    else:
        translation_result = await translate_video(video_path=video_path)
        # Save the translation result
        Path(video_path.replace('.mp4', '_translation.json')).write_text(translation_result.model_dump_json(indent=4), encoding='utf-8')

    # Annotate the video with the translated words
    annotate_video_with_highlighted_words_cv2_PIL(video_path,
                                                  translation_result,
                                                  subtitled_video_path)


async def get_video_and_output_paths(video_name: str) -> tuple[str, str, str]:
    video_path = f'{video_name}.mp4'
    subtitled_video_path = video_path.replace('.mp4', '_subtitled.mp4')
    translation_path = video_path.replace('.mp4', '_translation.json')
    if not Path(video_path).exists():
        raise FileNotFoundError(f"File not found: {video_path}")
    if not Path(video_path).is_file():
        raise ValueError(f"Path is not a file: {video_path}")
    return subtitled_video_path, video_path, translation_path


if __name__ == '__main__':
    import asyncio
    outer_video_name = str(Path("sample_data/sample_video_short/sample_video_short").resolve())
    # outer_video_name = "sample_data/sample_video_long/sample_video_long"
    asyncio.run(run_video_subtitle_pipeline(video_name=outer_video_name))
