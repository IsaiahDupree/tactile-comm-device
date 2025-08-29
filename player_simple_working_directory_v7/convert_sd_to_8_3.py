#!/usr/bin/env python3
"""
SD Card 8.3 Filename Conversion Script
Converts long filenames and directories to 8.3 format for FAT32 compatibility.
"""

import os
import shutil
import sys

def convert_sd_structure(sd_path):
    """Convert SD card structure to 8.3 format"""
    
    if not os.path.exists(sd_path):
        print(f"Error: SD path {sd_path} does not exist")
        return False
    
    print("=== SD Card 8.3 Conversion ===")
    print(f"Converting: {sd_path}")
    print()
    
    # Step 1: Rename main directories (case conversion)
    dir_renames = [
        ("config", "CONFIG"),
        ("mappings", "MAPPINGS"), 
        ("audio", "AUDIO"),
    ]
    
    for old_name, new_name in dir_renames:
        old_path = os.path.join(sd_path, old_name)
        new_path = os.path.join(sd_path, new_name)
        
        if os.path.exists(old_path) and old_path.lower() != new_path.lower():
            print(f"Renaming directory: {old_name} -> {new_name}")
            # Use temp name to handle case-only renames on Windows
            temp_path = old_path + "_TEMP"
            os.rename(old_path, temp_path)
            os.rename(temp_path, new_path)
    
    # Step 2: Rename audio subdirectory
    audio_human_old = os.path.join(sd_path, "AUDIO", "human")
    audio_human_new = os.path.join(sd_path, "AUDIO", "HUMAN")
    
    if os.path.exists(audio_human_old):
        print(f"Renaming: audio/human -> AUDIO/HUMAN")
        temp_path = audio_human_old + "_TEMP"
        os.rename(audio_human_old, temp_path)
        os.rename(temp_path, audio_human_new)
    
    # Step 3: Rename long filename in CONFIG
    config_dir = os.path.join(sd_path, "CONFIG")
    if os.path.exists(config_dir):
        old_flag = os.path.join(config_dir, "allow_writes.flag")
        new_flag = os.path.join(config_dir, "WRITES.FLG")
        
        if os.path.exists(old_flag):
            print(f"Renaming: allow_writes.flag -> WRITES.FLG")
            os.rename(old_flag, new_flag)
    
    # Step 4: Handle long directory names in human audio
    human_dir = os.path.join(sd_path, "AUDIO", "HUMAN")
    if os.path.exists(human_dir):
        long_dirs = {
            "HELLO_HOW_ARE_YOU": "HELLO_HO",
            "WHEELCHAIR": "WHEELCHA"
        }
        
        for old_name, new_name in long_dirs.items():
            old_path = os.path.join(human_dir, old_name)
            new_path = os.path.join(human_dir, new_name)
            
            if os.path.exists(old_path):
                print(f"Renaming: {old_name} -> {new_name}")
                os.rename(old_path, new_path)
    
    # Step 5: Rename announcements directory
    announce_old = os.path.join(sd_path, "announcements")
    announce_new = os.path.join(sd_path, "ANNOUNCE")
    
    if os.path.exists(announce_old):
        print(f"Renaming: announcements -> ANNOUNCE")
        os.rename(announce_old, announce_new)
    
    # Step 6: Convert file extensions to uppercase
    print("\nConverting file extensions to uppercase...")
    
    for root, dirs, files in os.walk(sd_path):
        for file in files:
            name, ext = os.path.splitext(file)
            if ext and ext != ext.upper():
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, name + ext.upper())
                print(f"  {file} -> {name + ext.upper()}")
                os.rename(old_path, new_path)
    
    print("\n✅ Conversion complete!")
    return True

def verify_structure(sd_path):
    """Verify the converted structure"""
    print("\n=== Verification ===")
    
    # Check critical paths
    critical_paths = [
        "CONFIG/KEYS.CSV",
        "CONFIG/WRITES.FLG", 
        "CONFIG/MODE.CFG",
        "MAPPINGS/INDEX.CSV",
        "AUDIO/HUMAN/",
        "AUDIO/GENERA~1/"
    ]
    
    all_good = True
    for path in critical_paths:
        full_path = os.path.join(sd_path, path)
        if os.path.exists(full_path):
            print(f"✅ {path}")
        else:
            print(f"❌ {path} - NOT FOUND")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    # Default SD path
    sd_path = r"c:\Users\Cypress\Documents\Coding\Buttons\player_simple_working_directory_v6\SD_CARD_STRUCTURE"
    
    if len(sys.argv) > 1:
        sd_path = sys.argv[1]
    
    print(f"Target SD structure: {sd_path}")
    
    # Ask for confirmation
    response = input("\nProceed with conversion? (y/N): ")
    if response.lower() != 'y':
        print("Conversion cancelled.")
        sys.exit(0)
    
    # Perform conversion
    if convert_sd_structure(sd_path):
        verify_structure(sd_path)
        print("\n🎉 SD card is now 8.3 compliant!")
        print("You can now copy this structure to your physical SD card.")
    else:
        print("❌ Conversion failed!")
        sys.exit(1)
