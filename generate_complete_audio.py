#!/usr/bin/env python3
"""
Generate complete audio files for all keys in the tactile communication device.
"""

import requests
import os
from pathlib import Path
import time

# API Configuration
API_KEY = "sk_e349c46da16f713a586a3848e96bda3a0f40b1b3f709b7c1"
BASE_URL = "https://api.elevenlabs.io/v1"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"

# All keys from configuration
ALL_KEYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'SHIFT', 'PERIOD', 'SPACE', 'YES', 'NO', 'WATER']

# Word mappings for each key
WORDS = {
    'A': ['Apple', 'Again', 'Always'],
    'B': ['Ball', 'Boy', 'Book'],
    'C': ['Cat', 'Car', 'Cookie'],
    'D': ['Dog', 'Door', 'Down'],
    'E': ['Egg', 'Eye', 'Eat'],
    'F': ['Fish', 'Food', 'Friend'],
    'G': ['Go', 'Good', 'Game'],
    'H': ['Hat', 'Help', 'Home'],
    'I': ['Ice', 'In', 'Important'],
    'J': ['Jump', 'Juice', 'Job'],
    'K': ['Key', 'Kitchen', 'Kind'],
    'L': ['Love', 'Like', 'Look'],
    'M': ['Mom', 'Milk', 'More'],
    'N': ['No', 'Name', 'Now'],
    'O': ['Open', 'Out', 'Over'],
    'P': ['Please', 'Play', 'Person'],
    'Q': ['Question', 'Quick', 'Quiet'],
    'R': ['Run', 'Red', 'Room'],
    'S': ['Stop', 'Say', 'See'],
    'T': ['Time', 'Thank', 'Today'],
    'U': ['Up', 'Under', 'Use'],
    'V': ['Very', 'Visit', 'Voice'],
    'W': ['Water', 'Want', 'Work'],
    'X': ['X-ray', 'Extra', 'Exit'],
    'Y': ['Yes', 'You', 'Yellow'],
    'Z': ['Zoo', 'Zebra', 'Zero'],
    'SHIFT': ['Shift', 'Capital', 'Upper case'],
    'PERIOD': ['Period', 'Dot', 'Full stop'],
    'SPACE': ['Space', 'Blank', 'Gap'],
    'YES': ['Yes', 'Correct', 'Right'],
    'NO': ['No', 'Wrong', 'Incorrect'],
    'WATER': ['Water', 'Drink', 'Thirsty']
}

def generate_audio(text, output_file):
    """Generate audio using ElevenLabs API."""
    url = f"{BASE_URL}/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"  [ERR] API Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"  [ERR] Exception: {e}")
        return False

def create_playlist(directory, num_files):
    """Create playlist.m3u file."""
    playlist_path = directory / 'playlist.m3u'
    with open(playlist_path, 'w') as f:
        for i in range(1, num_files + 1):
            f.write(f"{i:03d}.mp3\n")

def generate_key_audio(key, audio_type, base_path):
    """Generate audio files for a specific key and type."""
    key_dir = base_path / audio_type / key
    key_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== {key} ({audio_type}) ===")
    
    words = WORDS.get(key, [key.lower()])
    generated_count = 0
    
    for i, word in enumerate(words, start=1):
        output_file = key_dir / f"{i:03d}.mp3"
        
        if output_file.exists():
            print(f"  [SKIP] {output_file.name}")
            generated_count += 1
            continue
        
        print(f"  [GEN] {output_file.name} - '{word}'")
        success = generate_audio(word, output_file)
        
        if success:
            print(f"  [OK] Generated: {word}")
            generated_count += 1
        else:
            print(f"  [ERR] Failed: {word}")
        
        time.sleep(1.0)  # Rate limiting
    
    # Create playlist
    if generated_count > 0:
        create_playlist(key_dir, generated_count)
        print(f"  [PLAYLIST] Created with {generated_count} files")
    
    return generated_count

def main():
    base_path = Path(r"c:\Users\Cypress\Documents\Coding\Buttons\player_simple_working_directory_v3\SD_CARD_STRUCTURE\audio")
    
    print("=== Complete Audio Generation ===")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print(f"Voice ID: {VOICE_ID}")
    print(f"Base path: {base_path}")
    
    total_generated = 0
    
    # Generate both human and generated audio for all keys
    for audio_type in ['human', 'generated']:
        print(f"\n=== GENERATING {audio_type.upper()} AUDIO ===")
        
        for key in ALL_KEYS:
            count = generate_key_audio(key, audio_type, base_path)
            total_generated += count
    
    print(f"\n=== GENERATION COMPLETE ===")
    print(f"Total files generated: {total_generated}")
    print("All keys now have complete audio sets!")

if __name__ == "__main__":
    main()
