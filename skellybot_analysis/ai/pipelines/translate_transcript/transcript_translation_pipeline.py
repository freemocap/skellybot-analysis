import logging

from skellybot_analysis.ai.audio_transcription.translate_whisper_transcription import translate_transcription_result
from skellybot_analysis.ai.audio_transcription.whisper_transcription import transcribe_audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("numba").setLevel(logging.WARNING)

TARGET_LANGUAGES_W_ROMANIZATION = frozenset([("SPANISH", None),
                                             ("ARABIC-SCRIPT", "ALA-LC"),
                                             ("CHINESE-MANDARIN-SIMPLIFIED", "CHINESE-PINYIN")])


async def run_transcribe_and_translate_pipeline(audio_path: str,
                                                target_languages: set[tuple[str,str]] = TARGET_LANGUAGES_W_ROMANIZATION) -> None:
    print("pytorch.cuda.is_available():", torch.cuda.is_available())
    transcription_results = {}
    # Transcribe the MP3 file
    original_transcribed_result = transcribe_audio(audio_path)
    transcription_results[("ENGLISH", None)] = original_transcribed_result.text
    for target_language in target_languages:
        transcription_results[target_language] = await translate_transcription_result(
            original_transcription_text=original_transcribed_result.text,
            original_language="ENGLISH",
            target_language=target_language[0],
            romanization=target_language[1],
            verbose=False
            )
    # print(f"Original audio transcription: \n\t{original_transcribed_result.text}, "
    #       f"\n\n Translated text: \n\t{translation_result.translated_text}")

    out_str = ""
    for key, value in transcription_results.items():
        out_str += f"Target language: {key[0]}, Romanization:{key[1]}: \n\t{value}\n\n"
    print(out_str)
    with open("transcription_results.md", "w", encoding="utf-8") as f:
        f.write(out_str)


if __name__ == "__main__":
    import torch, asyncio

    print("torch.cuda.is_available():", torch.cuda.is_available())

    outer_audio_path = "voice-test.ogg"
    asyncio.run(run_transcribe_and_translate_pipeline(audio_path=outer_audio_path))
