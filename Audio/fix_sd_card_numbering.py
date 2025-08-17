#!/usr/bin/env python3
"""
Fix SD Card File Numbering

This script renames all word-named MP3 files to numbered format (001.mp3, 002.mp3, etc.)
for compatibility with the Arduino VS1053 tactile communicator code.
"""

import os
import glob
import shutil

def fix_folder_numbering(folder_path):
    """Fix file numbering in a single folder"""
    if not os.path.exists(folder_path):
        return
    
    # Get all MP3 files
    mp3_files = glob.glob(os.path.join(folder_path, "*.mp3"))
    mp3_files.sort()  # Sort alphabetically
    
    # Skip if already numbered correctly
    numbered_files = [f for f in mp3_files if os.path.basename(f).startswith(('001', '002', '003', '004', '005'))]
    if len(numbered_files) == len(mp3_files):
        print(f"✓ {folder_path} already correctly numbered")
        return
    
    # Create temporary directory for renaming
    temp_dir = os.path.join(folder_path, "_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Move all files to temp directory first
        temp_files = []
        for i, file_path in enumerate(mp3_files):
            temp_path = os.path.join(temp_dir, f"temp_{i:03d}.mp3")
            shutil.move(file_path, temp_path)
            temp_files.append(temp_path)
        
        # Move back with correct numbering
        for i, temp_path in enumerate(temp_files):
            final_path = os.path.join(folder_path, f"{i+1:03d}.mp3")
            shutil.move(temp_path, final_path)
            print(f"  Renamed: {os.path.basename(temp_path)} → {os.path.basename(final_path)}")
        
        # Remove temp directory
        os.rmdir(temp_dir)
        print(f"✓ Fixed numbering in {folder_path}")
        
    except Exception as e:
        print(f"✗ Error fixing {folder_path}: {e}")
        # Clean up temp directory if error
        if os.path.exists(temp_dir):
            for f in glob.glob(os.path.join(temp_dir, "*.mp3")):
                try:
                    shutil.move(f, folder_path)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass

def main():
    sd_path = "E:\\"
    
    if not os.path.exists(sd_path):
        print(f"Error: SD card not found at {sd_path}")
        return
    
    print("=== FIXING SD CARD FILE NUMBERING ===")
    print(f"SD Card: {sd_path}")
    print()
    
    # Fix numbering in folders 01-33
    for folder_num in range(1, 34):
        folder_name = f"{folder_num:02d}"
        folder_path = os.path.join(sd_path, folder_name)
        
        if os.path.exists(folder_path):
            print(f"Checking folder {folder_name}...")
            fix_folder_numbering(folder_path)
        else:
            print(f"Folder {folder_name} not found, skipping...")
    
    print()
    print("=== NUMBERING FIX COMPLETE ===")
    print("All audio files are now numbered 001.mp3, 002.mp3, etc.")
    print("Compatible with Arduino VS1053 tactile communicator code.")

if __name__ == "__main__":
    main()
