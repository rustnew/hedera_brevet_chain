# src/audio.py

from transformers import pipeline

asr = pipeline("automatic-speech-recognition", model="openai/whisper-small")

def audio_to_text(audio_path: str) -> str:
    return asr(audio_path)["text"]