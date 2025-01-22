from pathlib import Path

from moviepy import VideoFileClip, TextClip, CompositeVideoClip

from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translate_video import translate_video
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import \
    TranslatedTranscription, get_default_target_languages



def annotate_video_with_highlighted_words(video_path: str,
                                          transcription_result: TranslatedTranscription,
                                          output_path: str,
                                          ) -> None:

    # Load the video
    video = VideoFileClip(video_path)

    # Create word-level subtitle clips
    subtitle_clips = []
    for segment in transcription_result.segments:
        for word_timestamp in segment.words[:-1]:
            next_word_timestamp = segment.words[segment.words.index(word_timestamp) + 1]
            segment_words = segment.text.split()
            highlighted_text = ' '.join(
                [f"|{word}|"  if word in word_timestamp.word else f" {word} " for word in segment_words]
            )

            subtitle_clips.append(TextClip(text=highlighted_text,
                                           font_size=48,
                                           font='arial/ARIAL.TTF',
                                           color='white',
                                           bg_color=(0, 0, 0),
                                           stroke_width=2,
                                           method='caption',
                                           size=(video.w, 100),)
                                  .with_start(word_timestamp.start)
                                  .with_end(next_word_timestamp.start)
                                  .with_position(('center', video.h - 380))
                                  )

    # Combine the video with the highlighted subtitles
    final_video = CompositeVideoClip([video] + subtitle_clips).resized((1080,1920))
    # Write the result to a file
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')


async def run_video_subtitle_pipeline():
    video_path = r'auto_subtitler_test_video.mp4'
    output_path = r'auto_subtitler_test_output.mp4'


    if not Path(video_path).exists():
        raise FileNotFoundError(f"File not found: {video_path}")
    if not Path(video_path).is_file():
        raise ValueError(f"Path is not a file: {video_path}")

    translation_result = await translate_video(video_path=video_path,
                                               target_languages=get_default_target_languages())


    annotate_video_with_highlighted_words(video_path,
                                          translation_result,
                                          output_path)


if __name__ == '__main__':
    import asyncio
    asyncio.run(run_video_subtitle_pipeline())
