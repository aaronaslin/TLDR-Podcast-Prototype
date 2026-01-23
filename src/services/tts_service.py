"""TTS service wrapper."""
from datetime import datetime
from typing import Optional
from src.tts import synthesize_text_to_audio


def generate_audio(text: str, output_path: str, email_date: Optional[datetime] = None) -> str:
    return synthesize_text_to_audio(text, output_path, email_date=email_date)
