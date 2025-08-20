#!/usr/bin/env python3
"""
Copy human audio files from Recordings to SD card structure
"""

import os
import shutil
import json

def copy_human_audio():
    """Copy human recordings to SD card structure based on wordlist mapping"""
    
    # Load wordlist to understand structure
    with open('wordlist', 'r') as f:
        wordlist = json.load(f)
    
    recordings_dir = "Recordings"
    sd_base = "player_simple_working_directory_v4/SD_CARD_STRUCTURE/audio/human"
    
    # Mapping of recording files to wordlist keys
    file_mappings = {
        "Hello How are You.mp3": "SHIFT/001.mp3",
        "Good Morning.mp3": "GOOD/001.mp3",  # If GOOD exists in wordlist
        "I Love You.mp3": "I/001.mp3",
        "Bye.mp3": "BYE/001.mp3",  # If BYE exists in wordlist
        "Urgent Care.mp3": "URGENT/001.mp3",  # If URGENT exists in wordlist
        "Wheelchair.mp3": "WHEELCHAIR/001.mp3",  # If WHEELCHAIR exists in wordlist
        
        # Names - map to appropriate letters or create name directories
        "Alari.mp3": "A/001.mp3",
        "Amer.mp3": "A/002.mp3", 
        "Amory.mp3": "A/003.mp3",
        "Daddy.mp3": "D/001.mp3",
        "Deen.mp3": "D/002.mp3",
        "Kiyah.mp3": "K/001.mp3",
        "Kyan.mp3": "K/002.mp3",
        "Lee.mp3": "L/001.mp3",
        "Nada.mp3": "N/001.mp3",
        "Nadowie.mp3": "N/002.mp3",
        "Noah.mp3": "N/003.mp3",
        "Susu.mp3": "S/001.mp3",
        "Walker.mp3": "W/001.mp3"
    }
    
    copied_count = 0
    
    for source_file, target_path in file_mappings.items():
        source_path = os.path.join(recordings_dir, source_file)
        target_full_path = os.path.join(sd_base, target_path)
        
        if os.path.exists(source_path):
            # Create target directory if needed
            target_dir = os.path.dirname(target_full_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, target_full_path)
            print(f"✓ Copied: {source_file} → {target_path}")
            copied_count += 1
        else:
            print(f"✗ Missing: {source_file}")
    
    print(f"\nCopied {copied_count} human audio files to SD structure")

if __name__ == "__main__":
    copy_human_audio()
