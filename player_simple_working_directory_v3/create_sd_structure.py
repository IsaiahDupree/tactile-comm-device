#!/usr/bin/env python3
"""
Create SD Card Directory Structure for Manual Copy
This script creates a complete SD card directory structure with announcement files
"""

import os
import shutil
from pathlib import Path

def main():
    # Create SD card structure directory
    sd_structure_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SD_CARD_STRUCTURE")
    
    # Source audio files
    source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_announcements", "33")
    
    # Files to copy
    files_to_copy = [
        ("001.mp3", "Human first mode"),
        ("002.mp3", "Generated first mode")
    ]
    
    # Create directory structure
    directories_to_create = [
        "33",           # Primary location
        "audio",        # Fallback location 1
        "announcements" # Fallback location 2
        # Root directory (SD_CARD_STRUCTURE itself) will be fallback location 3
    ]
    
    print("Creating SD card directory structure...")
    
    # Create main structure directory
    os.makedirs(sd_structure_dir, exist_ok=True)
    print(f"Created: {sd_structure_dir}")
    
    # Create subdirectories
    for dir_name in directories_to_create:
        dir_path = os.path.join(sd_structure_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created: {dir_path}")
    
    # Copy files to all locations
    for filename, description in files_to_copy:
        source_file = os.path.join(source_dir, filename)
        
        if not os.path.exists(source_file):
            print(f"❌ Source file not found: {source_file}")
            continue
        
        print(f"\nCopying {filename} ({description})...")
        
        # Copy to primary location (/33/)
        target_file = os.path.join(sd_structure_dir, "33", filename)
        shutil.copy2(source_file, target_file)
        print(f"✅ Copied to: 33/{filename}")
        
        # Copy to fallback locations
        for dir_name in ["audio", "announcements"]:
            target_file = os.path.join(sd_structure_dir, dir_name, filename)
            shutil.copy2(source_file, target_file)
            print(f"✅ Copied to: {dir_name}/{filename}")
        
        # Copy to root (SD_CARD_STRUCTURE directory itself)
        target_file = os.path.join(sd_structure_dir, filename)
        shutil.copy2(source_file, target_file)
        print(f"✅ Copied to: root/{filename}")
    
    print(f"\n🎉 SD card structure created successfully!")
    print(f"\nTo use this:")
    print(f"1. Remove the SD card from your Arduino device")
    print(f"2. Insert it into your computer's card reader")
    print(f"3. Copy ALL contents from:")
    print(f"   {sd_structure_dir}")
    print(f"   TO your SD card root directory")
    print(f"4. Insert the SD card back into your Arduino device")
    print(f"5. Test priority mode toggle with 'M' command or triple-press period button")
    
    print(f"\nDirectory structure created:")
    print(f"SD_CARD_STRUCTURE/")
    print(f"├── 001.mp3              (root fallback)")
    print(f"├── 002.mp3              (root fallback)")
    print(f"├── 33/")
    print(f"│   ├── 001.mp3          (primary location)")
    print(f"│   └── 002.mp3          (primary location)")
    print(f"├── audio/")
    print(f"│   ├── 001.mp3          (fallback location)")
    print(f"│   └── 002.mp3          (fallback location)")
    print(f"└── announcements/")
    print(f"    ├── 001.mp3          (fallback location)")
    print(f"    └── 002.mp3          (fallback location)")

if __name__ == "__main__":
    main()
