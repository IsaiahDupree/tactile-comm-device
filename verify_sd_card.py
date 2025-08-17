#!/usr/bin/env python3
"""
Verify SD card is ready for tactile communication device.
Checks all expected audio files and configuration files are in place.
"""

import os
import json

SD_CARD_DRIVE = "E:\\"

# Expected recorded files based on our integration
EXPECTED_RECORDED_FILES = {
    "05": ["001.mp3", "002.mp3", "003.mp3"],  # A: Alari, Amer, Amory
    "08": ["001.mp3"],                        # D: Daddy
    "11": ["001.mp3"],                        # G: Good Morning
    "12": ["001.mp3"],                        # H: Hello How are You
    "15": ["001.mp3", "002.mp3"],             # K: Kiyah, Kyan
    "16": ["001.mp3", "002.mp3"],             # L: I Love You, Lee
    "18": ["001.mp3", "002.mp3", "003.mp3"],  # N: Nada, Nadowie, Noah
    "23": ["001.mp3"],                        # S: Susu
    "25": ["001.mp3"],                        # U: Urgent Care
    "27": ["001.mp3", "002.mp3"],             # W: Walker, Wheelchair
}

# Expected configuration files
EXPECTED_CONFIG_FILES = [
    "config/audio_index.csv",
    "config/audio_map.csv", 
    "config/buttons.csv",
    "AUDIO_MANIFEST.json"
]

def check_sd_card_ready():
    """Check if SD card is ready for tactile communication device."""
    print("🔍 VERIFYING SD CARD READINESS")
    print("=" * 50)
    
    if not os.path.exists(SD_CARD_DRIVE):
        print(f"❌ SD card not found at {SD_CARD_DRIVE}")
        return False
    
    all_good = True
    
    # Check recorded files
    print("\n📁 CHECKING RECORDED AUDIO FILES:")
    for folder, files in EXPECTED_RECORDED_FILES.items():
        folder_path = os.path.join(SD_CARD_DRIVE, folder)
        if not os.path.exists(folder_path):
            print(f"❌ Missing folder: /{folder}/")
            all_good = False
            continue
            
        for file in files:
            file_path = os.path.join(folder_path, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"✅ /{folder}/{file} ({size:,} bytes)")
            else:
                print(f"❌ Missing: /{folder}/{file}")
                all_good = False
    
    # Check configuration files
    print("\n📋 CHECKING CONFIGURATION FILES:")
    for config_file in EXPECTED_CONFIG_FILES:
        file_path = os.path.join(SD_CARD_DRIVE, config_file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {config_file} ({size:,} bytes)")
        else:
            print(f"❌ Missing: {config_file}")
            all_good = False
    
    # Check folder structure
    print("\n📂 CHECKING FOLDER STRUCTURE:")
    expected_folders = [f"{i:02d}" for i in range(1, 34)]  # 01-33
    missing_folders = []
    
    for folder in expected_folders:
        folder_path = os.path.join(SD_CARD_DRIVE, folder)
        if not os.path.exists(folder_path):
            missing_folders.append(folder)
    
    if missing_folders:
        print(f"❌ Missing folders: {', '.join(missing_folders)}")
        all_good = False
    else:
        print(f"✅ All 33 folders present (01-33)")
    
    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 SD CARD IS READY!")
        print("✅ All recorded files are in place")
        print("✅ All configuration files exist")
        print("✅ Folder structure is complete")
        print("\n🚀 Ready to upload Arduino firmware and test!")
    else:
        print("⚠️  SD CARD NEEDS ATTENTION")
        print("Some files or folders are missing.")
        print("Run organize_recorded_audio.py to fix issues.")
    
    print("=" * 50)
    return all_good

if __name__ == "__main__":
    check_sd_card_ready()
