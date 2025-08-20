#!/usr/bin/env python3
"""
Generate missing audio files for tactile communication device.
Creates both human and generated audio for missing keys.
"""

import os
import sys
from pathlib import Path
import time

# Add the current directory to Python path to import generate_audio
sys.path.append(str(Path(__file__).parent))

try:
    from generate_audio import generate_audio, DEFAULT_VOICE_ID, LETTER_WORDS
    print(f"✓ Loaded generate_audio module, voice: {DEFAULT_VOICE_ID}")
except ImportError as e:
    print(f"✗ Failed to import generate_audio: {e}")
    sys.exit(1)

# Define all keys from the configuration
ALL_KEYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'SHIFT', 'PERIOD', 'SPACE', 'YES', 'NO', 'WATER']

# Keys that currently have human audio
EXISTING_HUMAN = ['A', 'B', 'D', 'G', 'H', 'K', 'L', 'N', 'S', 'SHIFT', 'U', 'W']

# Special key mappings for non-letter keys
SPECIAL_WORDS = {
    'SHIFT': ['Shift', 'Capital', 'Upper case'],
    'PERIOD': ['Period', 'Dot', 'Full stop'],
    'SPACE': ['Space', 'Blank', 'Gap'],
    'YES': ['Yes', 'Correct', 'Right'],
    'NO': ['No', 'Wrong', 'Incorrect'],
    'WATER': ['Water', 'Drink', 'Thirsty']
}

def create_playlist(directory, num_files):
    """Create a playlist.m3u file for the given directory."""
    playlist_path = directory / 'playlist.m3u'
    with open(playlist_path, 'w') as f:
        for i in range(1, num_files + 1):
            f.write(f"{i:03d}.mp3\n")
    print(f"  Created playlist: {playlist_path}")

def generate_key_audio(key, audio_type, base_path, count=3):
    """Generate audio files for a specific key."""
    key_dir = base_path / audio_type / key
    key_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== Generating {audio_type} audio for {key} ===")
    
    # Determine words to generate
    if key in LETTER_WORDS:
        words = LETTER_WORDS[key][:count]
    elif key in SPECIAL_WORDS:
        words = SPECIAL_WORDS[key][:count]
    else:
        # Fallback for any missing keys
        words = [key.lower(), key.capitalize(), f"Letter {key}"][:count]
    
    generated_count = 0
    for i, word in enumerate(words, start=1):
        output_file = key_dir / f"{i:03d}.mp3"
        
        if output_file.exists():
            print(f"  [SKIP] {output_file.name} (already exists)")
            generated_count += 1
            continue
        
        print(f"  [GEN] {output_file.name} - '{word}'")
        success = generate_audio(word, DEFAULT_VOICE_ID, str(output_file))
        
        if success:
            print(f"  [OK] Generated: {word}")
            generated_count += 1
        else:
            print(f"  [ERR] Failed: {word}")
        
        # Rate limiting
        time.sleep(1.0)
    
    # Create playlist file
    if generated_count > 0:
        create_playlist(key_dir, generated_count)
    
    return generated_count

def main():
    # Base path for SD card structure
    sd_path = Path(r"c:\Users\Cypress\Documents\Coding\Buttons\player_simple_working_directory_v3\SD_CARD_STRUCTURE")
    audio_path = sd_path / "audio"
    
    print("=== Missing Audio File Generation ===")
    print(f"SD Path: {sd_path}")
    print(f"Voice ID: {DEFAULT_VOICE_ID}")
    
    # Find missing human audio keys
    missing_human = [key for key in ALL_KEYS if key not in EXISTING_HUMAN]
    print(f"\nMissing human audio for: {missing_human}")
    
    # Generate missing human audio
    print("\n=== GENERATING MISSING HUMAN AUDIO ===")
    for key in missing_human:
        generate_key_audio(key, "human", audio_path, count=3)
    
    # Check and fill any gaps in generated audio
    print("\n=== CHECKING GENERATED AUDIO ===")
    for key in ALL_KEYS:
        gen_dir = audio_path / "generated" / key
        if not gen_dir.exists() or len(list(gen_dir.glob("*.mp3"))) < 3:
            print(f"Filling generated audio for {key}")
            generate_key_audio(key, "generated", audio_path, count=3)
    
    print("\n=== Generation Complete ===")
    print("All missing audio files have been generated!")

if __name__ == "__main__":
    main()
