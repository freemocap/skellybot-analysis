import json
from pathlib import Path

from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip

from skellybot_analysis.ai.audio_transcription.whisper_transcription import transcribe_audio
from skellybot_analysis.models.data_models.whisper_transcript_result_full_model import WhisperTranscriptionResult


def annotate_video_with_highlighted_words(video_path: str,
                                          transcription_result: WhisperTranscriptionResult,
                                          output_path: str):
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
    final_video = CompositeVideoClip([video] + subtitle_clips)
    # Write the result to a file
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')


if __name__ == '__main__':
    # Example usage
    video_path = r'C:\Users\jonma\github_repos\freemocap_organization\skellybot-analysis\auto_subtitler_test_video.mp4'
    output_path = r'C:\Users\jonma\github_repos\freemocap_organization\skellybot-analysis\auto_subtitler_test_output.mp4'

    audio_path = r'C:\Users\jonma\github_repos\freemocap_organization\skellybot-analysis\auto_subtitler_test_audio.wav'
    transcript_path = r'C:\Users\jonma\github_repos\freemocap_organization\skellybot-analysis\auto_subtitler_test_transcript.json'

    if not Path(video_path).exists():
        raise FileNotFoundError(f"File not found: {video_path}")
    if not Path(video_path).is_file():
        raise ValueError(f"Path is not a file: {video_path}")


    # pull audio from video
    if not Path(transcript_path).exists():
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        transcription_result = transcribe_audio(audio_path)
        Path(transcript_path).write_text(transcription_result.model_dump_json(indent=2))
    else:
        json_text = Path(transcript_path).read_text()
        transcription_result = WhisperTranscriptionResult(**json.loads(json_text))

    annotate_video_with_highlighted_words(video_path, transcription_result, output_path)
