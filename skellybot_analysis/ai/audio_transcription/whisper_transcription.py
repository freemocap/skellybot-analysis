import asyncio
import logging
from pathlib import Path

import cv2
import whisper

from skellybot_analysis.ai.audio_transcription.models.simple_transcript_results_model import \
    SimpleWhisperTranscriptionResult
from skellybot_analysis.ai.audio_transcription.models.whisper_transcript_result_full_model import \
    WhisperTranscriptionResult
from skellybot_analysis.ai.pipelines.translate_transcript.transcript_translation_pipeline import \
    translate_transcription_result

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def validate_audio_path(audio_path: str) -> None:
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"File not found: {audio_path}")
    if not Path(audio_path).is_file():
        raise ValueError(f"Path is not a file: {audio_path}")
    if not Path(audio_path).suffix in [".mp3", ".ogg", ".wav"]:
        raise ValueError(f"Unsupported file format: {audio_path}")


def transcribe_audio(audio_path: str, model_name: str = "large") -> WhisperTranscriptionResult:
    validate_audio_path(audio_path)
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path,
                              word_timestamps=True,)
    return WhisperTranscriptionResult(**result)

def transcribe_audio_detailed(audio_path: str,
                                model_name: str = "turbo",
                              ):

    model = whisper.load_model(model_name)

    # validate/load audio and pad/trim it to fit 30 seconds
    validate_audio_path(audio_path)
    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)
    save_spectrogram_image(audio_path, mel)
    # detect the spoken language
    _, probs = model.detect_language(mel)
    print(f"Detected language: {max(probs, key=probs.get)}")

    # decode (transcribe) the audio
    transcription_result = whisper.decode(model=model,
                                          mel=mel,
                                          options=whisper.DecodingOptions())

    # print the recognized text
    print(transcription_result.text)
    return transcription_result


def save_spectrogram_image(audio_path, mel):
    mel_as_numpy = mel.cpu().numpy()
    mel_image = cv2.resize(mel_as_numpy, (4000, 1000))
    mel_image_scaled = cv2.normalize(mel_image, None, 0, 255, cv2.NORM_MINMAX)
    mel_image_heatmapped = cv2.applyColorMap(mel_image_scaled.astype('uint8'), cv2.COLORMAP_PLASMA)
    cv2.imwrite(str(Path(audio_path).with_suffix(".log_mel_spectrogram.png")), mel_image_heatmapped)


async def run_transcribe_and_translate_pipeline(audio_path: str):

    print("pytorch.cuda.is_available():", torch.cuda.is_available())
    # Transcribe the MP3 file
    transcribed_result = transcribe_audio(audio_path)
    simple_transcription_result = SimpleWhisperTranscriptionResult.from_whisper_transcription_result(transcribed_result)
    await translate_transcription_result(original_transcription_result=simple_transcription_result,
                                         original_language="ENGLISH",
                                         target_language="SPANISH",
                                         )
    # transcribed_result = transcribe_audio_detailed(audio_path)
    print(transcribed_result.text)


if __name__ == "__main__":
    import torch
    outer_audio_path = "voice-test.ogg"
    asyncio.run(run_transcribe_and_translate_pipeline(audio_path=outer_audio_path))
