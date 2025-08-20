#!/usr/bin/env python3
"""
Fix SD card audio structure to match wordlist definitions exactly
"""

import os
import json
import shutil

def create_proper_audio_structure():
    """Create audio directory structure matching wordlist exactly"""
    
    # Read the wordlist
    with open('wordlist', 'r') as f:
        wordlist = json.load(f)
    
    base_dir = "player_simple_working_directory_v4/SD_CARD_STRUCTURE/audio"
    
    # Clear existing structure
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    
    # Create base directories
    os.makedirs(f"{base_dir}/human", exist_ok=True)
    os.makedirs(f"{base_dir}/generated", exist_ok=True)
    
    print("Creating audio structure matching wordlist...")
    
    # Process letters A-Z
    for letter, data in wordlist["letters"].items():
        human_words = data.get("human", [])
        gen_words = data.get("generated", [])
        
        if human_words:
            human_dir = f"{base_dir}/human/{letter}"
            os.makedirs(human_dir, exist_ok=True)
            for i, word in enumerate(human_words, 1):
                filename = f"{i:03d}.mp3"
                txt_file = f"{human_dir}/{filename.replace('.mp3', '.txt')}"
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {filename} should contain: {word}\n")
        
        if gen_words:
            gen_dir = f"{base_dir}/generated/{letter}"
            os.makedirs(gen_dir, exist_ok=True)
            for i, word in enumerate(gen_words, 1):
                filename = f"{i:03d}.mp3"
                txt_file = f"{gen_dir}/{filename.replace('.mp3', '.txt')}"
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {filename} should contain: {word}\n")
        
        print(f"{letter}: {len(human_words)} human, {len(gen_words)} generated")
    
    # Process special phrases - SHIFT and HELLO_HOW_ARE_YOU are identical
    for phrase, data in wordlist["phrases"].items():
        human_words = data.get("human", [])
        gen_words = data.get("generated", [])
        
        if human_words:
            human_dir = f"{base_dir}/human/{phrase}"
            os.makedirs(human_dir, exist_ok=True)
            for i, word in enumerate(human_words, 1):
                filename = f"{i:03d}.mp3"
                txt_file = f"{human_dir}/{filename.replace('.mp3', '.txt')}"
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {filename} should contain: {word}\n")
        
        if gen_words:
            gen_dir = f"{base_dir}/generated/{phrase}"
            os.makedirs(gen_dir, exist_ok=True)
            for i, word in enumerate(gen_words, 1):
                filename = f"{i:03d}.mp3"
                txt_file = f"{gen_dir}/{filename.replace('.mp3', '.txt')}"
                with open(txt_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {filename} should contain: {word}\n")
        
        print(f"{phrase}: {len(human_words)} human, {len(gen_words)} generated")
    
    print("\nNote: SHIFT and HELLO_HOW_ARE_YOU have identical audio content")
    print("Both buttons will provide the same 4-press instruction functionality")
    
    print(f"\nFixed audio structure created in {base_dir}/")
    print("Replace .txt placeholder files with actual .mp3 audio files")
    print("Copy entire SD_CARD_STRUCTURE to your physical SD card")

if __name__ == "__main__":
    create_proper_audio_structure()
