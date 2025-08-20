#!/usr/bin/env python3
"""
Generate missing human audio files for tactile communication device.
"""

import os
import sys
from pathlib import Path
import time

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from generate_audio import generate_audio, DEFAULT_VOICE_ID, LETTER_WORDS
except ImportError as e:
    print(f"Error importing generate_audio: {e}")
    sys.exit(1)

# Special words for non-letter keys
SPECIAL_WORDS = {
    'SHIFT': ['Shift', 'Capital', 'Upper case'],
    'PERIOD': ['Period', 'Dot', 'Full stop'],
    'SPACE': ['Space', 'Blank', 'Gap'],
    'YES': ['Yes', 'Correct', 'Right'],
    'NO': ['No', 'Wrong', 'Incorrect'],
    'WATER': ['Water', 'Drink', 'Thirsty']
}

# Keys that need human audio generated
MISSING_HUMAN_KEYS = ['C', 'E', 'F', 'I', 'J', 'M', 'O', 'P', 'Q', 'R', 'T', 'V', 'X', 'Y', 'Z', 'PERIOD', 'SPACE', 'YES', 'NO', 'WATER']

def create_playlist(directory, num_files):
    """Create playlist.m3u file."""
    playlist_path = directory / 'playlist.m3u'
    with open(playlist_path, 'w') as f:
        for i in range(1, num_files + 1):
            f.write(f"{i:03d}.mp3\n")

def generate_key_audio(key, base_path):
    """Generate human audio for a specific key."""
    key_dir = base_path / key
    key_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== Generating human audio for {key} ===")
    
    # Get words for this key
    if key in LETTER_WORDS:
        words = LETTER_WORDS[key][:3]
    elif key in SPECIAL_WORDS:
        words = SPECIAL_WORDS[key][:3]
    else:
        words = [key.lower()]
    
    success_count = 0
    for i, word in enumerate(words, start=1):
        output_file = key_dir / f"{i:03d}.mp3"
        
        if output_file.exists():
            print(f"  [SKIP] {output_file.name}")
            success_count += 1
            continue
        
        print(f"  [GEN] {output_file.name} - '{word}'")
        success = generate_audio(word, DEFAULT_VOICE_ID, str(output_file))
        
        if success:
            print(f"  [OK] Generated: {word}")
            success_count += 1
        else:
            print(f"  [ERR] Failed: {word}")
        
        time.sleep(1.5)  # Rate limiting
    
    # Create playlist
    if success_count > 0:
        create_playlist(key_dir, success_count)
        print(f"  [PLAYLIST] Created with {success_count} files")
    
    return success_count

def main():
    base_path = Path(r"c:\Users\Cypress\Documents\Coding\Buttons\player_simple_working_directory_v3\SD_CARD_STRUCTURE\audio\human")
    
    print("=== Generating Missing Human Audio Files ===")
    print(f"Base path: {base_path}")
    print(f"Missing keys: {MISSING_HUMAN_KEYS}")
    
    total_generated = 0
    for key in MISSING_HUMAN_KEYS:
        count = generate_key_audio(key, base_path)
        total_generated += count
    
    print(f"\n=== Complete ===")
    print(f"Generated {total_generated} audio files")

if __name__ == "__main__":
    main()
