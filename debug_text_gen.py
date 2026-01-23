#!/usr/bin/env python3
"""
Debug script to generate and print processed text without running TTS.
"""
import os
import sys
from pathlib import Path

from src.config import Config
from src.email_ingest import get_latest_digest
from src.text_processor import clean_html_content, clean_text_for_tts
# Import the private function from tts module to simulate exact pipeline
from src.tts import _convert_to_formatted_text
from datetime import datetime
import re

def main():
    print("Fetching and processing text...")
    
    # Step 1: Fetch email
    email_result = get_latest_digest(
        Config.EMAIL_USERNAME,
        Config.EMAIL_PASSWORD,
        Config.EMAIL_SUBJECT_FILTER,
        Config.EMAIL_FOLDER,
        Config.EMAIL_SEARCH_BY,
        Config.IMAP_SERVER
    )
    
    if not email_result:
        print("✗ No matching emails found.")
        return

    if isinstance(email_result, tuple):
        email_body, _ = email_result
    else:
        email_body = email_result

    # Step 2: Process text
    cleaned_text = clean_html_content(email_body)
    tts_text_pre = clean_text_for_tts(cleaned_text, verbose=True)
    
    # Apply final TTS formatting
    tts_text_final = _convert_to_formatted_text(tts_text_pre)
    
    # -------------------------------------------------------------------------
    # Simulate the exact logic from src/tts.py _generate_audio_with_intro_outro_google
    # to reconstruct the full sequence of text sent to Google TTS
    # -------------------------------------------------------------------------
    
    headers = [
        'Headlines and Launches',
        'Deep Dives and Analysis',
        'Engineering and Research',
        'Miscellaneous',
        'Quick Links'
    ]
    
    header_indices = []
    for h in headers:
        pattern = re.escape(h)
        match = re.search(pattern, tts_text_final, re.IGNORECASE)
        if match:
            header_indices.append((match.start(), h))
            
    header_indices.sort(key=lambda x: x[0])
    
    final_segments = []
    
    # Intro Part
    if header_indices:
        first_header_idx = header_indices[0][0]
        intro_body = tts_text_final[0:first_header_idx].strip()
    else:
        intro_body = tts_text_final
        
    today_date = datetime.now()
    intro_script = f"Hello. You're listening to TLDR, AI Digest, the most interesting stories in the field of AI, {today_date.strftime('%A, %B %d')}. \n\nHere is your daily digest.\n\n{intro_body}"
    final_segments.append(intro_script)
    
    # Sections
    for i, (start_idx, header_name) in enumerate(header_indices):
        if i + 1 < len(header_indices):
            end_idx = header_indices[i+1][0]
        else:
            end_idx = len(tts_text_final)
            
        content = tts_text_final[start_idx:end_idx].strip()
        final_segments.append(content)
        
    # Outro
    outro_script = "That concludes today's briefing. If you enjoyed this episode, please leave a like or a rating on your favorite podcast app.\n\nWe'll be back tomorrow with more updates. \nThanks for listening to TLDR, AI Digest."
    final_segments.append(outro_script)
    
    full_audio_script = "\n\n".join(final_segments)
    
    output_path = "output/processed_text.txt"
    Path("output").mkdir(exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(full_audio_script)
        
    print(f"✓ Processed text saved to: {output_path}")
    print("-" * 50)
    print(full_audio_script)
    print("-" * 50)

if __name__ == "__main__":
    main()
