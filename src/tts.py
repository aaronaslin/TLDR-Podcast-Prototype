"""
Text-to-Speech module using Google Cloud Text-to-Speech (Vertex AI Voice) with advanced audio mixing.
Supports intro/outro music, section chimes, and voice adjustments.
"""
import asyncio
import os
import re
import shutil
import json
from datetime import datetime
import html as html_lib
import io

from google.cloud import texttospeech
from src.config import Config

from pydub import AudioSegment
from pydub.effects import normalize

# Ensure ffmpeg/ffprobe are found for pydub
FFMPEG_PATH = shutil.which("ffmpeg")
FFPROBE_PATH = shutil.which("ffprobe")

if not FFMPEG_PATH or not FFPROBE_PATH:
    raise RuntimeError(
        "ffmpeg and ffprobe are required but not found in PATH.\n"
        "Please install ffmpeg:\n"
        "  macOS: brew install ffmpeg\n"
        "  Ubuntu/Debian: apt-get install ffmpeg\n"
        "  Windows: download from https://ffmpeg.org/download.html"
    )

AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH


def synthesize_text_to_audio(text, output_filename, email_date=None):
    """
    Convert text to audio using Google Cloud TTS API with intro and outro.
    
    Args:
        text (str): Text content to convert to speech
        output_filename (str): Path where MP3 file should be saved
        email_date (datetime, optional): The date of the email digest. Defaults to None.
        
    Returns:
        str: Path to the generated audio file
    """
    _generate_audio_with_intro_outro_google(text, output_filename, email_date)
    return output_filename


def _setup_google_client():
    """Initialize Google Cloud TTS Client."""
    if Config.GCS_CREDENTIALS_FILE and os.path.exists(Config.GCS_CREDENTIALS_FILE):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = Config.GCS_CREDENTIALS_FILE
    return texttospeech.TextToSpeechClient()


def _synthesize_text_google(client, text):
    """
    Synthesize a text chunk using Google Cloud TTS.
    Handles text longer than 5000 bytes by splitting recursively.
    """
    # 1. Clean/Format text slightly if needed, but assuming input is ready.
    # Google limits: 5000 bytes. 
    # Use 4500 as a safe limit.
    LIMIT = 4500
    
    if len(text.encode('utf-8')) <= LIMIT:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=Config.GOOGLE_TTS_LANGUAGE_CODE,
            name=Config.GOOGLE_TTS_VOICE_NAME
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=Config.GOOGLE_TTS_SPEAKING_RATE,
            pitch=Config.GOOGLE_TTS_PITCH
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # Load directly into AudioSegment
        return AudioSegment.from_file(io.BytesIO(response.audio_content), format="mp3")
    else:
        # Split text
        # Try to split by double newline (paragraph)
        split_idx = text.rfind('\n\n', 0, LIMIT)
        if split_idx == -1:
             # Try single newline
            split_idx = text.rfind('\n', 0, LIMIT)
        if split_idx == -1:
            # Try period
            split_idx = text.rfind('. ', 0, LIMIT)
        if split_idx == -1:
            # Hard split
            split_idx = LIMIT
            
        part1 = text[:split_idx]
        part2 = text[split_idx:].lstrip()
        
        audio1 = _synthesize_text_google(client, part1)
        audio2 = _synthesize_text_google(client, part2)
        return audio1 + audio2


def _generate_audio_with_intro_outro_google(text, output_filename, email_date=None):
    """
    Generate audio with intro and outro using Google Cloud TTS.
    Splits text by headers to insert chimes between sections.
    """
    client = _setup_google_client()
    
    # 1. Prepare Text
    formatted_text = _convert_to_formatted_text(text)
    
    # Identify Key Sections
    # We will split the formatted_text based on known headers.
    headers = [
        'Headlines and Launches',
        'Deep Dives and Analysis',
        'Engineering and Research',
        'Miscellaneous',
        'Quick Links'
    ]
    
    header_indices = []
    for h in headers:
        # Search for "Header." or just "Header" (header + period often added by formatter)
        pattern = re.escape(h)
        match = re.search(pattern, formatted_text, re.IGNORECASE)
        if match:
            header_indices.append((match.start(), h))
            
    header_indices.sort(key=lambda x: x[0])
    
    sections = []
    
    # Intro Part (before first header)
    if header_indices:
        first_header_idx = header_indices[0][0]
        intro_body = formatted_text[0:first_header_idx].strip()
    else:
        intro_body = formatted_text
        
    date_to_use = email_date if email_date else datetime.now()
    intro_script = f"Hello. You're listening to TLDR AI Digest, the most interesting stories in the field of AI, {date_to_use.strftime('%A, %B %d')}. \n\nHere is your daily digest.\n\n{intro_body}"
    
    sections.append(('Intro', intro_script))
    
    for i, (start_idx, header_name) in enumerate(header_indices):
        # End index is the start of the next header, or end of string
        if i + 1 < len(header_indices):
            end_idx = header_indices[i+1][0]
        else:
            end_idx = len(formatted_text)
            
        content = formatted_text[start_idx:end_idx].strip()
        sections.append((header_name, content))
        
    outro_script = "That concludes today's briefing. If you enjoyed this episode, please leave a like or a rating on your favorite podcast app.\n\nWe'll be back tomorrow with more updates. \nThanks for listening to TLDR AI Digest."
    
    # 2. Synthesize
    audio_segments = []
    
    # Chime Setup
    chime_audio = None
    if Config.SECTION_CHIME_FILE and os.path.exists(Config.SECTION_CHIME_FILE):
        chime_audio = AudioSegment.from_file(Config.SECTION_CHIME_FILE)
        chime_audio = chime_audio - (20 * (1 - Config.SECTION_CHIME_VOLUME))
        
    # Process Loop
    for idx, (section_name, section_text) in enumerate(sections):
        print(f"Synthesizing section: {section_name}...")
        
        # Add Chime (if not Intro)
        if idx > 0 and chime_audio:
             audio_segments.append(chime_audio)
             audio_segments.append(AudioSegment.silent(duration=300))
             
        if not section_text.strip():
            continue
            
        segment_audio = _synthesize_text_google(client, section_text)
        audio_segments.append(segment_audio)
        
        # Add silence after section
        audio_segments.append(AudioSegment.silent(duration=500))
        
    print("Synthesizing outro...")
    outro_audio = _synthesize_text_google(client, outro_script)
    audio_segments.append(outro_audio)
    
    # Outro Music (Play AFTER text)
    if Config.OUTRO_MUSIC_FILE and os.path.exists(Config.OUTRO_MUSIC_FILE):
        outro_music = AudioSegment.from_file(Config.OUTRO_MUSIC_FILE)
        outro_music = outro_music[:Config.OUTRO_MUSIC_DURATION * 1000]
        outro_music = outro_music - (20 * (1 - Config.OUTRO_MUSIC_VOLUME))
        outro_music = outro_music.fade_in(500).fade_out(1500)
        
        audio_segments.append(outro_music)
    
    # 3. Combine All
    full_audio = sum(audio_segments, AudioSegment.empty())
    
    # 4. Intro Music (Lead In)
    if Config.INTRO_MUSIC_FILE and os.path.exists(Config.INTRO_MUSIC_FILE):
        intro_music = AudioSegment.from_file(Config.INTRO_MUSIC_FILE)
        intro_music = intro_music - (20 * (1 - Config.INTRO_MUSIC_VOLUME))
        lead_in_ms = Config.INTRO_MUSIC_LEAD_IN * 1000
        music_lead = intro_music[:lead_in_ms]
        
        full_audio = music_lead + full_audio

    # 5. Export
    full_audio = normalize(full_audio)
    full_audio.export(output_filename, format="mp3", bitrate="192k")


def _convert_to_formatted_text(text):
    """
    Format plain text for better TTS cadence using strategic punctuation and line breaks.
    """
    # Decode HTML entities
    text = html_lib.unescape(text)

    # Clean up artifacts that might cause TTS issues
    text = text.replace('*', ' ')  # Remove asterisks
    text = text.replace('`', ' ')  # Remove backticks
    text = text.replace('_', ' ')  # Remove underscores
    text = text.replace('—', ', ') # Normalize em-dash to comma
    text = text.replace('–', '-')  # Normalize en-dash to hyphen
    
    # Remove bracketed markup
    text = re.sub(r"\[([^\]]+)\]", r"\1", text)

    # Replace bare ampersands
    text = re.sub(r"\s*&\s*", " and ", text)

    # Abbreviations
    text = re.sub(r"\bU\.S\.\b", "US", text)
    text = re.sub(r"\bU\.K\.\b", "UK", text)
    text = re.sub(r"\be\.g\.\b", "for example", text, flags=re.IGNORECASE)
    text = re.sub(r"\bi\.e\.\b", "that is", text, flags=re.IGNORECASE)
    text = re.sub(r"(\d+)%", r"\1 percent", text)
    
    # Pronunciation helpers
    text = re.sub(r"\bOpenAI\b", "Open A I", text, flags=re.IGNORECASE)
    text = re.sub(r"\b([A-Z])\.\s*([A-Z])\.\s*([A-Za-z])", r"\1\2 \3", text)
    text = re.sub(r"(\w+)\s+prod-?ready\b", r"\1, product ready", text, flags=re.IGNORECASE)

    # Currency normalization
    def _money_sub(m):
        amount = m.group(1)
        suffix = (m.group(2) or "").lower()
        if suffix == 'b':
            return f"{amount} billion dollars"
        if suffix == 'm':
            return f"{amount} million dollars"
        if suffix == 'k':
            return f"{amount} thousand dollars"
        return f"{amount} dollars"

    text = re.sub(r"\$(\d+(?:\.\d+)?)([BbMmKk])?\b", _money_sub, text)

    # Parentheticals
    text = re.sub(r"\(([^)]+)\)", r", \1,", text)

    # List-intro lines
    text = re.sub(r"\byou get:\s+", "you get. ", text, flags=re.IGNORECASE)
    text = re.sub(r":\s*\n\s*\n\s*(?=[A-Z0-9])", ":\n", text) # Colon fix

    # TLDR dots
    text = re.sub(r"(?<=[A-Z])\.{2,}(?=\s+[A-Z])", " ", text)
    text = re.sub(r"(?<=[a-z0-9])\.{2,}(?=\s+[A-Z])", ". ", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\?{2,}", "?", text)
    text = re.sub(r"!{2,}", "!", text)

    # Bullet prefixes
    text = re.sub(r"(^|\n)\s*[•\-*]\s+", r"\1", text)
    # Spaced apostrophes
    text = re.sub(r"\s+'\s*([a-zA-Z])", r"'\1", text)
    text = re.sub(r"([a-zA-Z])\s+'\s*([a-zA-Z])", r"\1'\2", text)

    # Split into paragraphs to re-format
    paragraphs = re.split(r"\n\s*\n+", text)
    formatted_parts = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Remove single line breaks inside paragraph
        para = re.sub(r"\s*\n\s*", " ", para)
        para = re.sub(r"\s+", " ", para).strip()

        # Header detection
        is_header = (
            len(para) < 80 and
            (para.isupper() or para.endswith(':') or para.count(' ') < 6)
        )

        if is_header:
            # Section headers: keep brief and punctuated for a natural pause
            header = para.rstrip(':')
            formatted_parts.append(f"{header}.")
        else:
            # Join sentences with spaces to let Google TTS handle natural pausing based on punctuation.
            # We already collapsed newlines in the paragraph above.
            formatted_parts.append(para)

    return "\n\n".join([p for p in formatted_parts if p.strip()])
