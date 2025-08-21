#!/usr/bin/env python3
"""
Generate TTS audio files from wordlist.json using ElevenLabs API.
Creates organized folder structure with clear, understandable audio files.
"""

import json
import os
from pathlib import Path
import time
import sys

# Get API key from environment
if not os.getenv('ELEVENLABS_API_KEY'):
    print("Error: ELEVENLABS_API_KEY environment variable not set")
    print("Set it with: export ELEVENLABS_API_KEY='your_key_here'")
    sys.exit(1)

try:
    from generate_audio import generate_audio, DEFAULT_VOICE_ID
    print(f"✓ Loaded generate_audio module, voice: {DEFAULT_VOICE_ID}")
except ImportError as e:
    print(f"✗ Failed to import generate_audio: {e}")
    sys.exit(1)


def sanitize_filename(text):
    """Convert text to safe filename, preserving readability."""
    # Replace problematic characters but keep spaces and basic punctuation readable
    safe = text.replace('/', '_').replace('\\', '_').replace(':', '_')
    safe = safe.replace('*', '_').replace('?', '_').replace('"', '_')
    safe = safe.replace('<', '_').replace('>', '_').replace('|', '_')
    # Limit length but keep meaningful
    if len(safe) > 100:
        safe = safe[:97] + "..."
    return safe


def generate_letter_audio(letter, generated_words, output_dir):
    """Generate audio files for a letter's generated words."""
    letter_dir = output_dir / "letters" / letter
    letter_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== Generating audio for letter {letter} ===")
    
    for i, word in enumerate(generated_words, 1):
        filename = f"{i:03d}_{sanitize_filename(word)}.mp3"
        output_path = letter_dir / filename
        
        if output_path.exists():
            print(f"  [SKIP] {filename} (already exists)")
            continue
            
        print(f"  [GEN] {filename}")
        success = generate_audio(word, DEFAULT_VOICE_ID, str(output_path))
        
        if success:
            print(f"  [OK] Generated: {word}")
        else:
            print(f"  [ERR] Failed: {word}")
            
        # Rate limiting - be gentle with API
        time.sleep(0.5)


def generate_phrase_audio(phrase_key, generated_texts, output_dir):
    """Generate audio files for phrase generated texts."""
    phrase_dir = output_dir / "phrases" / phrase_key
    phrase_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=== Generating audio for phrase {phrase_key} ===")
    
    for i, text in enumerate(generated_texts, 1):
        filename = f"{i:03d}_{sanitize_filename(text)}.mp3"
        output_path = phrase_dir / filename
        
        if output_path.exists():
            print(f"  [SKIP] {filename} (already exists)")
            continue
            
        print(f"  [GEN] {filename}")
        success = generate_audio(text, DEFAULT_VOICE_ID, str(output_path))
        
        if success:
            print(f"  [OK] Generated: {text[:50]}{'...' if len(text) > 50 else ''}")
        else:
            print(f"  [ERR] Failed: {text[:50]}{'...' if len(text) > 50 else ''}")
            
        # Rate limiting - be gentle with API
        time.sleep(0.5)


def main():
    # Paths
    wordlist_path = Path("wordlist")
    output_dir = Path("Generated_Audio")
    
    # Load wordlist
    if not wordlist_path.exists():
        print(f"ERROR: {wordlist_path} not found!")
        return 1
        
    with open(wordlist_path, 'r', encoding='utf-8') as f:
        wordlist = json.load(f)
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print(f"=== TTS Audio Generation from Wordlist ===")
    print(f"Voice ID: {DEFAULT_VOICE_ID}")
    print(f"Output directory: {output_dir.absolute()}")
    
    # Generate letter audio
    letters = wordlist.get("letters", {})
    for letter, banks in letters.items():
        generated_words = banks.get("generated", [])
        if generated_words:
            generate_letter_audio(letter, generated_words, output_dir)
    
    # Generate phrase audio
    phrases = wordlist.get("phrases", {})
    for phrase_key, banks in phrases.items():
        generated_texts = banks.get("generated", [])
        if generated_texts:
            generate_phrase_audio(phrase_key, generated_texts, output_dir)
    
    print(f"\n=== Generation Complete ===")
    print(f"Audio files saved to: {output_dir.absolute()}")
    print("Folder structure:")
    print("  Generated_Audio/")
    print("    letters/")
    print("      A/, B/, C/, ... (each with numbered MP3s)")
    print("    phrases/")
    print("      SPACE/, PERIOD/, HELLO_HOW_ARE_YOU/ (each with numbered MP3s)")
    
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
