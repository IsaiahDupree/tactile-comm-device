#!/usr/bin/env python3
"""
SD Card Setup Script for Tactile Communication Device

This script organizes the generated audio files into the proper folder structure
for the DFPlayer Mini module, which requires specific folder numbering.

Folder Structure:
01/ - Special buttons (YES, NO, WATER, AUX)
02/ - Letter A
03/ - Letter B
...
27/ - Letter Z
28/ - Punctuation (SPACE, PERIOD)
"""

import json
import shutil
import os
from pathlib import Path

def setup_sd_structure(sd_path):
    """Create and populate SD card folder structure"""
    
    sd_path = Path(sd_path)
    if not sd_path.exists():
        print(f"Error: SD card path {sd_path} does not exist")
        return False
    
    print(f"Setting up SD card at: {sd_path}")
    
    # Load the audio index
    with open('11labs/audio_index.json', 'r') as f:
        audio_index = json.load(f)
    
    # Create folder structure
    folders_created = 0
    files_copied = 0
    
    # Special buttons -> Folder 01
    special_folder = sd_path / "01"
    special_folder.mkdir(exist_ok=True)
    
    track_num = 1
    for button in ["YES", "NO", "WATER", "AUX"]:
        if button in audio_index["audio_files"]:
            for audio_file in audio_index["audio_files"][button]:
                src_file = Path("11labs") / audio_file["file"]
                dst_file = special_folder / f"{track_num:03d}.mp3"
                
                if src_file.exists():
                    shutil.copy2(src_file, dst_file)
                    print(f"✓ {button}: {src_file.name} → {dst_file}")
                    files_copied += 1
                    track_num += 1
    
    folders_created += 1
    
    # Letters A-Z -> Folders 02-27
    for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        folder_num = i + 2  # A=02, B=03, etc.
        letter_folder = sd_path / f"{folder_num:02d}"
        
        if letter in audio_index["audio_files"]:
            letter_folder.mkdir(exist_ok=True)
            
            track_num = 1
            for audio_file in audio_index["audio_files"][letter]:
                src_file = Path("11labs") / audio_file["file"]
                dst_file = letter_folder / f"{track_num:03d}.mp3"
                
                if src_file.exists():
                    shutil.copy2(src_file, dst_file)
                    print(f"✓ {letter}: {src_file.name} → {dst_file}")
                    files_copied += 1
                    track_num += 1
            
            folders_created += 1
    
    # Punctuation -> Folder 28
    punct_folder = sd_path / "28"
    punct_folder.mkdir(exist_ok=True)
    
    track_num = 1
    for punct in ["SPACE", "PERIOD"]:
        if punct in audio_index["audio_files"]:
            for audio_file in audio_index["audio_files"][punct]:
                src_file = Path("11labs") / audio_file["file"]
                dst_file = punct_folder / f"{track_num:03d}.mp3"
                
                if src_file.exists():
                    shutil.copy2(src_file, dst_file)
                    print(f"✓ {punct}: {src_file.name} → {dst_file}")
                    files_copied += 1
                    track_num += 1
    
    folders_created += 1
    
    print(f"\n=== SD Card Setup Complete ===")
    print(f"✓ Created {folders_created} folders")
    print(f"✓ Copied {files_copied} audio files")
    print(f"✓ Ready for DFPlayer Mini")
    
    return True

def create_sd_mapping_file(sd_path):
    """Create a reference file showing the SD card mapping"""
    
    mapping_content = """# SD Card Audio File Mapping
# For DFPlayer Mini Module

## Folder Structure:

### Folder 01 - Special Buttons
001.mp3 - Yes
002.mp3 - No  
003.mp3 - Water
004.mp3 - Hello How are You

### Folder 02 - Letter A
001.mp3 - Amer
002.mp3 - Alari
003.mp3 - Apple
004.mp3 - Arabic Show

### Folder 03 - Letter B
001.mp3 - Bathroom
002.mp3 - Bye
003.mp3 - Bed
004.mp3 - Breathe
005.mp3 - blanket

### Folder 04 - Letter C
001.mp3 - Chair
002.mp3 - car
003.mp3 - Cucumber

### Folder 05 - Letter D
001.mp3 - Deen
002.mp3 - Daddy
003.mp3 - Doctor
004.mp3 - Door

### Folder 07 - Letter F
001.mp3 - FaceTime
002.mp3 - funny

### Folder 08 - Letter G
001.mp3 - Good Morning
002.mp3 - Go

### Folder 09 - Letter H
001.mp3 - How are you
002.mp3 - Heartburn

### Folder 10 - Letter I
001.mp3 - Inside

### Folder 12 - Letter K
001.mp3 - Kiyah
002.mp3 - Kyan
003.mp3 - Kleenex
004.mp3 - Kaiser

### Folder 13 - Letter L
001.mp3 - Lee
002.mp3 - I love you
003.mp3 - light down
004.mp3 - light up

### Folder 14 - Letter M
001.mp3 - Mohammad
002.mp3 - Medicine
003.mp3 - Medical

### Folder 15 - Letter N
001.mp3 - Nada
002.mp3 - Nadowie
003.mp3 - Noah

### Folder 16 - Letter O
001.mp3 - Outside

### Folder 17 - Letter P
001.mp3 - Pain
002.mp3 - Phone

### Folder 19 - Letter R
001.mp3 - Room

### Folder 20 - Letter S
001.mp3 - Scarf
002.mp3 - Susu
003.mp3 - Sinemet

### Folder 21 - Letter T
001.mp3 - TV

### Folder 22 - Letter U
001.mp3 - Urgent Care

### Folder 24 - Letter W
001.mp3 - Water
002.mp3 - Walker
003.mp3 - wheelchair
004.mp3 - walk

### Folder 28 - Punctuation
001.mp3 - space
002.mp3 - period

## Arduino Code Reference:
```
myDFPlayer.playFolder(folder_number, track_number);
```

Example: To play "Amer" → myDFPlayer.playFolder(2, 1);
Example: To play "I love you" → myDFPlayer.playFolder(13, 2);
"""
    
    mapping_file = Path(sd_path) / "AUDIO_MAPPING.txt"
    with open(mapping_file, 'w') as f:
        f.write(mapping_content)
    
    print(f"✓ Created mapping reference: {mapping_file}")

def main():
    print("SD Card Setup for Tactile Communication Device")
    print("=" * 50)
    
    # Check if audio files exist
    if not Path("11labs/audio_index.json").exists():
        print("❌ Audio files not found. Run 'python generate_audio.py' first.")
        return
    
    # Get SD card path from user
    sd_path = input("Enter SD card drive path (e.g., E:\\ or /media/sdcard): ").strip()
    
    if not sd_path:
        print("❌ No path provided. Exiting.")
        return
    
    # Setup SD card
    if setup_sd_structure(sd_path):
        create_sd_mapping_file(sd_path)
        print("\n🎉 SD card is ready for the tactile communication device!")
        print("Insert the SD card into your DFPlayer Mini module.")
    else:
        print("❌ SD card setup failed.")

if __name__ == "__main__":
    main()
