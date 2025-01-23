import logging
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from tqdm import tqdm

from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.language_models import LanguageNames
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.transcribe_video import \
    scrape_and_save_audio_from_video
from skellybot_analysis.ai.pipelines.translate_transcript_pipeline.translated_transcript_model import \
    TranslatedTranscription

logger = logging.getLogger(__name__)


def create_multiline_text(text: str, font: ImageFont, screen_width: int, buffer: int) -> str:
    """
    Break a long string into multiple lines of text that fit within the screen width by inserting `\n` characters
    at appropriate locations. to ensure the text will fit within the screen width with `buffer` pixels of padding on each side.
    will use `font.getlength('word1 + ' + 'word2' ...) method to determine when to break lines.

    :param text: The text to break into multiple lines
    :param font: The font to use for the text
    :param screen_width: The width of the screen
    :param buffer: The number of pixels of padding to leave on each side of the text
    """
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if font.getlength(current_line + ' ' + word) + 2 * buffer < screen_width:
            current_line += ' ' + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return '\n'.join(lines)


def finish_video_and_attach_audio_from_original(original_video_path: str,
                                                no_audio_video_path: str,
                                                subtitled_video_path: str) -> None:
    # Save the audio from the original video to a wav file (if it doesn't already exist)
    original_audio_path = original_video_path.replace('.mp4', '.wav')
    if not Path(original_audio_path).exists():
        scrape_and_save_audio_from_video(original_video_path, original_audio_path)

    # Compress and combine the audio from the original video with the annotated video
    command = (
        f"ffmpeg -y -i {no_audio_video_path} -i {original_audio_path} "
        f"-c:v libx264 -crf 23 -preset fast -c:a aac -strict experimental "
        f"{subtitled_video_path}"
    )
    logger.info(f"Combining and compressing video and audio with ffmpeg command - {command}")
    os.system(command)

    # Delete the no-audio temporary video file
    try:
        os.remove(no_audio_video_path)
        logger.info(f"Deleted temporary no-audio video file: {no_audio_video_path}")
    except OSError as e:
        logger.error(f"Error deleting temporary video file {no_audio_video_path}: {e}")


def annotate_video_with_highlighted_words_cv2_PIL(video_path: str,
                                                  transcription_result: TranslatedTranscription,
                                                  subtitled_video_path: str,
                                                  show_while_annotating: bool = True
                                                  ) -> None:
    # Load the video
    if not Path(video_path).exists() or not Path(video_path).is_file():
        raise FileNotFoundError(f"File not found: {video_path}")
    video_reader = cv2.VideoCapture(video_path)
    video_width = int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_resolution = (video_width, video_height)
    video_framerate = video_reader.get(cv2.CAP_PROP_FPS)
    video_number_of_frames = int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT))

    Path(subtitled_video_path).parent.mkdir(parents=True, exist_ok=True)
    if not subtitled_video_path.endswith('.mp4'):
        raise ValueError(f"Output path must end with .mp4: {subtitled_video_path}")
    no_audio_video_path = subtitled_video_path.replace('.mp4', '_no_audio.mp4')

    video_writer = cv2.VideoWriter(no_audio_video_path, cv2.VideoWriter_fourcc(*'x264'), video_framerate,
                                   video_resolution)
    if not video_writer.isOpened():
        raise ValueError(f"Failed to open video writer: {subtitled_video_path}")

    # font path
    font_path = Path(__file__).parent.parent.parent.parent.parent.parent / "fonts/arial/ARIAL.TTF"
    if not font_path.exists() or not font_path.is_file():
        raise FileNotFoundError(f"Font not found: {font_path}")
    font_path = str(font_path)
    font_size = 48
    buffer_size = 100
    arial_font = ImageFont.truetype(font_path, font_size)

    try:
        # Go through each frame of the video and annotate it with the translated words based on their timestamps
        for frame_number in tqdm(range(video_number_of_frames), desc="Annotating video with subtitles",
                                 total=video_number_of_frames):
            if not video_reader.isOpened():
                raise ValueError(f"Video reader is not open: {video_path}")

            read_success, image = video_reader.read()
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            if not read_success or not video_reader.isOpened():
                break
            frame_number += 1
            frame_timestamp = video_reader.get(
                cv2.CAP_PROP_POS_MSEC) / 1000  # seconds - internally based on frame# * presumed frame duration based on specified framerate
            pil_image = Image.fromarray(image)
            image_annotator = ImageDraw.Draw(pil_image)

            current_segment, current_word = transcription_result.get_segment_and_word_at_timestamp(frame_timestamp)
            for language_name in [LanguageNames.ENGLISH.value, LanguageNames.SPANISH.value, LanguageNames.CHINESE_MANDARIN_SIMPLIFIED.value, LanguageNames.ARABIC_LEVANTINE.value]:
                multiline_y_start = get_y_start_by_language(language_name, video_height)

                segment_text = current_segment.get_text_by_language(language_name)
                word_text = current_word.get_word_by_language(language_name)
                segment_words = segment_text.split()
                highlighted_segment_words = [f"[{word}]" if word_text.strip() in word.strip() else word for word in segment_words]
                highlighted_segment_text = ' '.join(highlighted_segment_words)
                multiline_text = create_multiline_text(highlighted_segment_text,
                                                       arial_font,
                                                       video_width,
                                                       buffer_size)

                # Annotate the frame with the current segment using PIL
                image_annotator.multiline_text(xy=(buffer_size, multiline_y_start),
                                               text=multiline_text,
                                               fill=(255,0, 155),
                                               stroke_width=3,
                                               stroke_fill=(0, 0, 0),
                                               font=arial_font)




            # Convert the annotated image back to a cv2 image and write it to the video
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            if not video_writer.isOpened():
                raise ValueError(f"Video writer is not open: {subtitled_video_path}")
            video_writer.write(image)
            if not video_writer.isOpened():
                raise ValueError(f"Video writer is not open: {subtitled_video_path}")

            if show_while_annotating:
                max_length = 720
                if max(image.shape[:2]) > max_length:
                    scale_factor = max_length / max(image.shape[:2])
                    display_image = cv2.resize(image, (0, 0), fx=scale_factor, fy=scale_factor)
                else:
                    display_image = image
                cv2.imshow(str(Path(video_path).stem), display_image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    finally:
        video_reader.release()
        video_writer.release()
        finish_video_and_attach_audio_from_original(original_video_path=video_path,
                                                    no_audio_video_path=no_audio_video_path,
                                                    subtitled_video_path=subtitled_video_path)
        cv2.destroyAllWindows()


def get_y_start_by_language(language_name, video_height):
    if language_name == LanguageNames.ENGLISH.value:
        multiline_y_start = 0
    elif language_name == LanguageNames.SPANISH.value:
        multiline_y_start = video_height // 4
    elif language_name == LanguageNames.CHINESE_MANDARIN_SIMPLIFIED.value:
        multiline_y_start = video_height // 2
    elif language_name == LanguageNames.ARABIC_LEVANTINE.value:
        multiline_y_start = video_height // 4 * 3
    else:
        raise ValueError(f"Unsupported language name: {language_name}")
    return multiline_y_start
