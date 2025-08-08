# src/translate.py

from transformers import pipeline

translator = pipeline("translation", model="facebook/nllb-200-distilled-600M")

def translate_to_english(text: str) -> str:
    result = translator(text, src_lang="fra_Latn", tgt_lang="eng_Latn")
    return result[0]['translation_text']