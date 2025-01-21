import logging
from pathlib import Path

import whisper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def validate_audio_path(audio_path: str) -> None:
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"File not found: {audio_path}")
    if not Path(audio_path).is_file():
        raise ValueError(f"Path is not a file: {audio_path}")
    if not Path(audio_path).suffix in [".mp3", ".ogg", ".wav"]:
        raise ValueError(f"Unsupported file format: {audio_path}")


def transcribe_audio(audio_path: str, model_name: str = "large") -> str:
    validate_audio_path(audio_path)
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)
    return result

import whisper

def transcribe_audio_detailed(audio_path: str,
                                model_name: str = "large",
                              ):

    model = whisper.load_model(model_name)
    validate_audio_path(audio_path)

    # load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)

    # detect the spoken language
    _, probs = model.detect_language(mel)
    print(f"Detected language: {max(probs, key=probs.get)}")

    # decode the audio
    options = whisper.DecodingOptions()
    result = whisper.decode(model, mel, options)

    # print the recognized text
    print(result.text)

if __name__ == "__main__":
    audio_path = "./voice-test.ogg"


    # Transcribe the MP3 file
    transcribed_text = transcribe_audio(audio_path)
    print(transcribed_text)