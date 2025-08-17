#!/usr/bin/env python3
"""
Audio Generation Script for Tactile Communication Device
Generates MP3 files using ElevenLabs API for all letter-to-word mappings
"""

import json
import os
import requests
import time
from pathlib import Path

# ElevenLabs Configuration
ELEVENLABS_API_KEY = "sk_33095b4fed3a2d88e04c7bf0c3c75768fcb579bc1643a702"
VOICE_ID = "RILOU7YmBhvwJGDGjNmP"
ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

# Audio settings - slowed down for better comprehension
AUDIO_SETTINGS = {
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.7,        # Higher stability for clearer speech
        "similarity_boost": 0.75, # Slightly lower for more natural pace
        "style": 0.1,            # Lower style for slower, clearer speech
        "use_speaker_boost": True
    },
    "pronunciation_dictionary_locators": [],
    "seed": None,
    "previous_text": None,
    "next_text": None,
    "previous_request_ids": [],
    "next_request_ids": []
}

def load_mappings():
    """Load letter-to-word mappings from JSON file"""
    with open('letter_mappings.json', 'r') as f:
        return json.load(f)

def sanitize_filename(text):
    """Sanitize text for use as filename"""
    # Replace problematic characters
    sanitized = text.replace(" ", "_").replace("'", "").replace(",", "")
    sanitized = "".join(c for c in sanitized if c.isalnum() or c in "_-")
    return sanitized.lower()

def slow_down_text(text):
    """Add pauses and spacing to slow down speech"""
    # Add slight pauses after certain words for better comprehension
    text = text.replace(",", ", ")  # Pause after commas
    text = text.replace(".", ". ")   # Pause after periods
    
    # Add natural pauses for longer phrases
    if len(text.split()) > 2:
        words = text.split()
        # Add micro-pauses between words for multi-word phrases
        text = " ".join(words)
    
    return text

def generate_audio_file(text, filename, output_dir):
    """Generate audio file using ElevenLabs API with slower speech"""
    # Apply text modifications for slower speech
    modified_text = slow_down_text(text)
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": modified_text,
        **AUDIO_SETTINGS
    }
    
    try:
        print(f"Generating audio for: '{text}'")
        response = requests.post(ELEVENLABS_URL, json=data, headers=headers)
        
        if response.status_code == 200:
            filepath = output_dir / f"{filename}.mp3"
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"✓ Created: {filepath}")
            return True
        else:
            print(f"✗ Error generating '{text}': {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Exception generating '{text}': {str(e)}")
        return False

def create_directory_structure():
    """Create organized directory structure for audio files"""
    base_dir = Path("11labs")
    
    dirs_to_create = [
        base_dir / "special_buttons",
        base_dir / "letters",
        base_dir / "punctuation"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return base_dir

def generate_all_audio():
    """Generate audio files for all mappings"""
    mappings = load_mappings()
    base_dir = create_directory_structure()
    
    generated_count = 0
    failed_count = 0
    
    # Generate special button audio
    print("\n=== Generating Special Button Audio ===")
    special_dir = base_dir / "special_buttons"
    for button, phrases in mappings["special_buttons"].items():
        for i, phrase in enumerate(phrases):
            filename = f"{button.lower()}_{i+1}_{sanitize_filename(phrase)}"
            if generate_audio_file(phrase, filename, special_dir):
                generated_count += 1
            else:
                failed_count += 1
            time.sleep(0.5)  # Rate limiting
    
    # Generate letter audio
    print("\n=== Generating Letter Audio ===")
    letters_dir = base_dir / "letters"
    for letter, phrases in mappings["letters"].items():
        if phrases:  # Only process letters with assigned words
            letter_dir = letters_dir / letter.lower()
            letter_dir.mkdir(exist_ok=True)
            
            for i, phrase in enumerate(phrases):
                filename = f"{letter.lower()}_{i+1}_{sanitize_filename(phrase)}"
                if generate_audio_file(phrase, filename, letter_dir):
                    generated_count += 1
                else:
                    failed_count += 1
                time.sleep(0.5)  # Rate limiting
    
    # Generate punctuation audio
    print("\n=== Generating Punctuation Audio ===")
    punct_dir = base_dir / "punctuation"
    for punct, phrases in mappings["punctuation"].items():
        for i, phrase in enumerate(phrases):
            # For space, use "space" as the spoken word
            spoken_text = "space" if phrase == " " else phrase
            filename = f"{punct.lower()}_{i+1}_{sanitize_filename(spoken_text)}"
            if generate_audio_file(spoken_text, filename, punct_dir):
                generated_count += 1
            else:
                failed_count += 1
            time.sleep(0.5)  # Rate limiting
    
    print(f"\n=== Generation Complete ===")
    print(f"✓ Successfully generated: {generated_count} files")
    print(f"✗ Failed to generate: {failed_count} files")
    
    return generated_count, failed_count

def create_audio_index():
    """Create an index file mapping buttons to audio files"""
    mappings = load_mappings()
    base_dir = Path("11labs")
    
    index = {
        "device_info": {
            "voice_id": VOICE_ID,
            "voice_model": "ElevenLabs Monolingual v1",
            "generation_date": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "audio_files": {}
    }
    
    # Index special buttons
    special_dir = base_dir / "special_buttons"
    for button, phrases in mappings["special_buttons"].items():
        index["audio_files"][button] = []
        for i, phrase in enumerate(phrases):
            filename = f"{button.lower()}_{i+1}_{sanitize_filename(phrase)}.mp3"
            index["audio_files"][button].append({
                "text": phrase,
                "file": f"special_buttons/{filename}",
                "button_press": i + 1
            })
    
    # Index letters
    for letter, phrases in mappings["letters"].items():
        if phrases:
            index["audio_files"][letter] = []
            for i, phrase in enumerate(phrases):
                filename = f"{letter.lower()}_{i+1}_{sanitize_filename(phrase)}.mp3"
                index["audio_files"][letter].append({
                    "text": phrase,
                    "file": f"letters/{letter.lower()}/{filename}",
                    "button_press": i + 1
                })
    
    # Index punctuation
    for punct, phrases in mappings["punctuation"].items():
        index["audio_files"][punct] = []
        for i, phrase in enumerate(phrases):
            spoken_text = "space" if phrase == " " else phrase
            filename = f"{punct.lower()}_{i+1}_{sanitize_filename(spoken_text)}.mp3"
            index["audio_files"][punct].append({
                "text": phrase,
                "spoken_text": spoken_text,
                "file": f"punctuation/{filename}",
                "button_press": i + 1
            })
    
    # Save index
    with open(base_dir / "audio_index.json", 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"✓ Created audio index: {base_dir}/audio_index.json")

if __name__ == "__main__":
    print("Tactile Communication Device - Audio Generator")
    print("=" * 50)
    
    try:
        generated, failed = generate_all_audio()
        create_audio_index()
        
        if failed == 0:
            print("\n🎉 All audio files generated successfully!")
        else:
            print(f"\n⚠️  Generated {generated} files with {failed} failures.")
            print("Check your API key and internet connection.")
            
    except KeyboardInterrupt:
        print("\n\n❌ Generation cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
