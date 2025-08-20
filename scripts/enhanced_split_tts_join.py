#!/usr/bin/env python3
"""
Enhanced version: Split SHIFT mapping text into parts, synthesize with ElevenLabs at slow speed,
and join into MP3. Includes better pacing, error handling, and direct MP3 output.

Usage:
  python scripts/enhanced_split_tts_join.py \
    --input-text "Full word list mapping. I will speak slowly..." \
    --out-dir "test_output/shift_split" \
    --final-mp3 "player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio/GENERA~1/SHIFT/004.mp3" \
    --api-key "sk_..."
"""

import argparse
import os
import re
import sys
import time
import json
import tempfile
from pathlib import Path
import requests
from io import BytesIO

ELEVEN_BASE_URL = "https://api.elevenlabs.io/v1"


def enhance_pacing(text: str) -> str:
    """Add strategic pauses for slower, clearer delivery"""
    # Add longer pauses after periods
    text = re.sub(r'\.(\s+)', r'. ... ', text)
    # Add pauses after colons (letter introductions)
    text = re.sub(r':(\s+)', r': ... ', text)
    # Add breathing pauses after "Take a breath" and similar
    text = re.sub(r'(Take a breath|Breathe|Pause)\.', r'\1. ... ... ', text)
    # Add extra pause before major sections
    text = re.sub(r'(Now, the letters\.|End of list\.|Reminder\.)', r'... \1', text)
    return text


def split_into_logical_parts(full_text: str) -> list[str]:
    """
    Split into 4 logical parts with better boundaries:
    Part 1: Intro + A-F
    Part 2: G-M  
    Part 3: N-S
    Part 4: T-Z + Closing
    """
    # Find letter positions
    letter_positions = {}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        pattern = rf'\b{letter}:'
        match = re.search(pattern, full_text)
        if match:
            letter_positions[letter] = match.start()
    
    # Define split points
    split_letters = ['A', 'G', 'N', 'T']
    parts = []
    
    if all(letter in letter_positions for letter in split_letters):
        # Use letter-based splits
        boundaries = [0] + [letter_positions[letter] for letter in split_letters[1:]] + [len(full_text)]
        
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            part = full_text[start:end].strip()
            parts.append(part)
    else:
        # Fallback to length-based quarters
        length = len(full_text)
        quarter = length // 4
        for i in range(4):
            start = i * quarter
            end = (i + 1) * quarter if i < 3 else length
            parts.append(full_text[start:end].strip())
    
    return parts


def tts_to_mp3_bytes(text: str, api_key: str, voice_id: str = "RILOU7YmBhvwJGDGjNmP", 
                     model_id: str = "eleven_monolingual_v1") -> bytes | None:
    """Generate MP3 audio bytes using ElevenLabs API with slow, clear settings"""
    
    url = f"{ELEVEN_BASE_URL}/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json", 
        "xi-api-key": api_key,
    }
    
    # Optimized settings for slow, clear speech
    body = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.7,        # Higher stability for consistent pace
            "similarity_boost": 0.6, # Good voice consistency
            "style": 0.1,           # Lower style for clearer speech
            "use_speaker_boost": True
        }
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=60)
        if response.status_code == 200:
            print(f"✓ Generated audio ({len(response.content)} bytes)")
            return response.content
        else:
            print(f"✗ TTS failed ({response.status_code}): {response.text[:200]}")
            return None
    except Exception as e:
        print(f"✗ TTS error: {e}")
        return None


def concatenate_mp3_bytes(mp3_parts: list[bytes]) -> bytes:
    """Simple MP3 concatenation (works for most cases without complex frame analysis)"""
    if not mp3_parts:
        return b''
    
    # For basic concatenation, we just join the bytes
    # This works well when all parts have similar encoding settings
    return b''.join(mp3_parts)


def main():
    parser = argparse.ArgumentParser(description="Enhanced split/TTS/join for SHIFT mapping")
    parser.add_argument("--input-text", required=True, help="Full text to split and synthesize")
    parser.add_argument("--out-dir", default="test_output/shift_split", help="Directory for intermediate files")
    parser.add_argument("--final-mp3", required=True, help="Output path for final MP3")
    parser.add_argument("--api-key", required=True, help="ElevenLabs API key")
    parser.add_argument("--voice-id", default="RILOU7YmBhvwJGDGjNmP", help="ElevenLabs voice ID")
    parser.add_argument("--backup-original", action="store_true", help="Backup existing MP3 before replacing")
    
    args = parser.parse_args()
    
    # Enhance text pacing
    enhanced_text = enhance_pacing(args.input_text)
    print(f"Enhanced text length: {len(enhanced_text)} characters")
    
    # Split into parts
    parts = split_into_logical_parts(enhanced_text)
    print(f"Split into {len(parts)} parts: {[len(p) for p in parts]} characters each")
    
    # Create output directory
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate audio for each part
    mp3_parts = []
    for i, part in enumerate(parts, 1):
        print(f"\nGenerating part {i}/{len(parts)}...")
        
        # Save text part
        part_file = out_dir / f"part_{i:02d}.txt"
        part_file.write_text(part, encoding="utf-8")
        
        # Generate audio
        mp3_bytes = tts_to_mp3_bytes(part, args.api_key, args.voice_id)
        if mp3_bytes is None:
            print(f"Failed to generate audio for part {i}")
            return 1
            
        # Save individual MP3
        part_mp3 = out_dir / f"part_{i:02d}.mp3"
        part_mp3.write_bytes(mp3_bytes)
        print(f"✓ Saved {part_mp3}")
        
        mp3_parts.append(mp3_bytes)
        
        # Rate limiting
        time.sleep(0.8)
    
    # Concatenate all parts
    print(f"\nCombining {len(mp3_parts)} audio parts...")
    combined_mp3 = concatenate_mp3_bytes(mp3_parts)
    
    # Backup original if requested
    final_path = Path(args.final_mp3)
    if args.backup_original and final_path.exists():
        backup_path = final_path.with_suffix('.backup.mp3')
        backup_path.write_bytes(final_path.read_bytes())
        print(f"✓ Backed up original to {backup_path}")
    
    # Write final MP3
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_bytes(combined_mp3)
    
    print(f"✓ Final MP3 saved: {final_path}")
    print(f"✓ Size: {len(combined_mp3):,} bytes")
    print(f"✓ Estimated duration: ~{len(combined_mp3) / 16000:.1f} minutes")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
