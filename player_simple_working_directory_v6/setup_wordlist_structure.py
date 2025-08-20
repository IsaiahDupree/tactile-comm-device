#!/usr/bin/env python3
"""
Generate SD card directory structure for v4 directory-based audio system
Based on wordlist.json mapping with proper 001.mp3, 002.mp3 naming
"""

import os
import json
import shutil

def create_audio_directories():
    """Create the complete audio directory structure based on wordlist"""
    
    # Read the wordlist
    wordlist_path = "../wordlist"
    with open(wordlist_path, 'r') as f:
        wordlist = json.load(f)
    
    base_dir = "SD_CARD_STRUCTURE/audio"
    
    # Create base directories
    os.makedirs(f"{base_dir}/human", exist_ok=True)
    os.makedirs(f"{base_dir}/generated", exist_ok=True)
    
    # Process letters A-Z
    for letter, data in wordlist["letters"].items():
        print(f"Creating directories for {letter}...")
        
        # Human audio directory
        human_dir = f"{base_dir}/human/{letter}"
        os.makedirs(human_dir, exist_ok=True)
        
        # Create numbered placeholder files for human audio
        human_words = data.get("human", [])
        for i, word in enumerate(human_words, 1):
            filename = f"{i:03d}.mp3"
            filepath = f"{human_dir}/{filename}"
            if not os.path.exists(filepath):
                # Create placeholder file with comment about the word
                with open(filepath.replace('.mp3', '.txt'), 'w') as f:
                    f.write(f"# {filename} should contain: {word}\n")
        
        # Generated audio directory
        gen_dir = f"{base_dir}/generated/{letter}"
        os.makedirs(gen_dir, exist_ok=True)
        
        # Create numbered placeholder files for generated audio
        gen_words = data.get("generated", [])
        for i, word in enumerate(gen_words, 1):
            filename = f"{i:03d}.mp3"
            filepath = f"{gen_dir}/{filename}"
            if not os.path.exists(filepath):
                # Create placeholder file with comment about the word
                with open(filepath.replace('.mp3', '.txt'), 'w') as f:
                    f.write(f"# {filename} should contain: {word}\n")
    
    # Process special phrases
    for phrase, data in wordlist["phrases"].items():
        print(f"Creating directories for {phrase}...")
        
        # Human audio directory
        human_dir = f"{base_dir}/human/{phrase}"
        os.makedirs(human_dir, exist_ok=True)
        
        # Create numbered placeholder files for human audio
        human_words = data.get("human", [])
        for i, word in enumerate(human_words, 1):
            filename = f"{i:03d}.mp3"
            filepath = f"{human_dir}/{filename}"
            if not os.path.exists(filepath):
                with open(filepath.replace('.mp3', '.txt'), 'w') as f:
                    f.write(f"# {filename} should contain: {word}\n")
        
        # Generated audio directory
        gen_dir = f"{base_dir}/generated/{phrase}"
        os.makedirs(gen_dir, exist_ok=True)
        
        # Create numbered placeholder files for generated audio
        gen_words = data.get("generated", [])
        for i, word in enumerate(gen_words, 1):
            filename = f"{i:03d}.mp3"
            filepath = f"{gen_dir}/{filename}"
            if not os.path.exists(filepath):
                with open(filepath.replace('.mp3', '.txt'), 'w') as f:
                    f.write(f"# {filename} should contain: {word}\n")

def print_summary():
    """Print a summary of the directory structure created"""
    print("\n" + "="*60)
    print("DIRECTORY STRUCTURE CREATED")
    print("="*60)
    
    wordlist_path = "../wordlist"
    with open(wordlist_path, 'r') as f:
        wordlist = json.load(f)
    
    print("\nLetters with audio:")
    for letter, data in wordlist["letters"].items():
        human_count = len(data.get("human", []))
        gen_count = len(data.get("generated", []))
        print(f"  {letter}: {human_count} human, {gen_count} generated")
    
    print("\nSpecial phrases:")
    for phrase, data in wordlist["phrases"].items():
        human_count = len(data.get("human", []))
        gen_count = len(data.get("generated", []))
        print(f"  {phrase}: {human_count} human, {gen_count} generated")
    
    print(f"\nNext steps:")
    print(f"1. Upload the v4 sketch to your Arduino")
    print(f"2. Replace .txt placeholder files with actual .mp3 audio")
    print(f"3. Copy SD_CARD_STRUCTURE to your physical SD card")
    print(f"4. Test multi-press functionality")

if __name__ == "__main__":
    create_audio_directories()
    print_summary()
