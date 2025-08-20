#!/usr/bin/env python3
"""
Copy SHIFT generated audio files from D: drive to SD card structure
"""

import os
import shutil
from pathlib import Path

def copy_shift_audio():
    # Source: D drive generated SHIFT files
    source_dir = Path("D:/audio/generated/SHIFT")
    
    # Destination: SD card structure (update this path to match your SD card)
    dest_dir = Path("C:/Users/Cypress/Documents/Coding/Buttons/player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio/generated/SHIFT")
    
    print(f"Copying SHIFT generated audio files...")
    print(f"From: {source_dir}")
    print(f"To: {dest_dir}")
    
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all audio files from source to destination
    if source_dir.exists():
        for file in source_dir.glob("*"):
            if file.is_file() and file.suffix.lower() in ['.mp3', '.wav', '.txt']:
                dest_file = dest_dir / file.name
                shutil.copy2(file, dest_file)
                print(f"Copied: {file.name}")
    else:
        print(f"ERROR: Source directory {source_dir} does not exist!")
        return False
    
    print("✓ SHIFT audio files copied successfully!")
    
    # List what's now in the destination
    print(f"\nFiles now in {dest_dir}:")
    for file in sorted(dest_dir.glob("*")):
        print(f"  - {file.name}")
    
    return True

if __name__ == "__main__":
    copy_shift_audio()
