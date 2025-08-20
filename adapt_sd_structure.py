#!/usr/bin/env python3
"""
Adapt SD card folder structure to match FAT32 8.3 naming that Arduino sees
"""

import os
import shutil
from pathlib import Path

def adapt_sd_structure():
    # Paths
    base_path = Path("C:/Users/Cypress/Documents/Coding/Buttons/player_simple_working_directory_v5/SD_CARD_STRUCTURE/audio")
    d_drive_path = Path("D:/audio/generated/SHIFT")
    genera_path = base_path / "GENERA~1"
    shift_path = genera_path / "SHIFT"
    
    print("Adapting SD card structure to match Arduino FAT32 8.3 naming...")
    
    # Create GENERA~1 directory structure
    genera_path.mkdir(exist_ok=True)
    shift_path.mkdir(exist_ok=True)
    
    # Copy SHIFT files from D: drive if it exists
    if d_drive_path.exists():
        print(f"Copying SHIFT files from {d_drive_path} to {shift_path}")
        for file in d_drive_path.glob("*"):
            dest = shift_path / file.name
            shutil.copy2(file, dest)
            print(f"  Copied: {file.name} ({file.stat().st_size} bytes)")
    else:
        print(f"D: drive path not found: {d_drive_path}")
        # Create placeholder files for testing
        files_to_create = [
            ("002.mp3", 46856, "Generated instructions audio"),
            ("002.txt", 684, "Instructions for using the tactile communication device"),
            ("003.mp3", 652479, "Generated word list audio"),
            ("003.txt", 1132, "Complete word list for tactile communication"),
            ("004.mp3", 887790, "Additional generated content"),
            ("004.txt", 977, "Additional tactile communication content")
        ]
        
        for filename, size, content in files_to_create:
            file_path = shift_path / filename
            if filename.endswith('.txt'):
                file_path.write_text(content)
            else:
                # Create dummy MP3 file of approximate size
                with open(file_path, 'wb') as f:
                    f.write(b'\x00' * size)
            print(f"  Created: {filename} ({size} bytes)")
    
    # List final structure
    print(f"\nFinal structure:")
    print(f"  {base_path}/")
    print(f"    human/")
    print(f"    GENERA~1/  ← Arduino sees this instead of 'generated'")
    print(f"      SHIFT/")
    
    if shift_path.exists():
        for file in sorted(shift_path.glob("*")):
            print(f"        {file.name} ({file.stat().st_size} bytes)")
    
    print(f"\n✓ SD card structure adapted for FAT32 8.3 compatibility")
    print("Arduino will now find files at: /audio/GENERA~1/SHIFT/")

if __name__ == "__main__":
    adapt_sd_structure()
