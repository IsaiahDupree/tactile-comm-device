#!/usr/bin/env python3
"""
Copy human recordings from Recordings folder to SD card structure
"""

import os
import shutil

def copy_recordings():
    """Copy recordings to SD card human audio structure"""
    
    recordings_dir = "Recordings"
    sd_human_dir = "player_simple_working_directory_v4/SD_CARD_STRUCTURE/audio/human"
    
    # Direct mappings based on available recordings
    mappings = {
        "Hello How are You.mp3": "SHIFT/001.mp3",
        "Good Morning.mp3": "G/001.mp3",
        "I Love You.mp3": "L/001.mp3",
        "Bye.mp3": "B/001.mp3",
        "Urgent Care.mp3": "U/001.mp3",
        "Wheelchair.mp3": "W/001.mp3",
        
        # Names mapped to letters
        "Alari.mp3": "A/001.mp3",
        "Amer.mp3": "A/002.mp3", 
        "Amory.mp3": "A/003.mp3",
        "Daddy.mp3": "D/001.mp3",
        "Deen.mp3": "D/002.mp3",
        "Kiyah.mp3": "K/001.mp3",
        "Kyan.mp3": "K/002.mp3",
        "Lee.mp3": "L/002.mp3",
        "Nada.mp3": "N/001.mp3",
        "Nadowie.mp3": "N/002.mp3",
        "Noah.mp3": "N/003.mp3",
        "Susu.mp3": "S/001.mp3",
        "Walker.mp3": "W/002.mp3"
    }
    
    copied_count = 0
    
    for source_file, target_path in mappings.items():
        source_full = os.path.join(recordings_dir, source_file)
        target_full = os.path.join(sd_human_dir, target_path)
        
        if os.path.exists(source_full):
            # Create target directory
            os.makedirs(os.path.dirname(target_full), exist_ok=True)
            
            # Copy file
            shutil.copy2(source_full, target_full)
            print(f"✓ {source_file} → {target_path}")
            copied_count += 1
        else:
            print(f"✗ Missing: {source_file}")
    
    print(f"\nCopied {copied_count} human recordings to SD structure")

if __name__ == "__main__":
    copy_recordings()
